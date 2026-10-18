"""Question browsing must keep native widget usage bounded on large CSVs."""

import os
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch

from trivia_countdown.gui import QuestionTable, TriviaCountdownApp, quote_cli_argument
from trivia_countdown.lib.models import TriviaQuestion


class QuestionBrowserTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.selections = []
        self.table = QuestionTable(self.root, self.selections.append)
        self.question = TriviaQuestion("Question", ("One", "Two", "Three", "Four"), 2)

    def test_large_collection_bounds_widgets_and_uses_global_question_numbers(self):
        self.table.set_questions([self.question] * 10_003)
        self.assertEqual(len(self.table._row_widgets), 25)
        self.assertEqual(len(self.table._content.winfo_children()), 26 * 7)
        self.assertTrue(self.table._previous_button.instate(["disabled"]))
        old_label = self.table._row_widgets[0][0]
        self.table._next_button.invoke()
        self.assertFalse(old_label.winfo_exists())
        self.assertEqual(self.table._row_widgets[0][0].cget("text"), "26")
        self.assertEqual(len(self.table._content.winfo_children()), 26 * 7)
        self.table.select(25)
        self.assertEqual(self.selections, [25])
        self.assertEqual(self.table._row_widgets[0][0].cget("background"), "#d9f2df")
        self.table._previous_button.invoke()
        self.assertEqual(self.selections, [25])
        self.table._next_button.invoke()
        self.assertEqual(self.table._row_widgets[0][0].cget("background"), "#d9f2df")

        self.table.select(10_002)
        self.assertEqual(self.selections[-1], 10_002)
        self.assertEqual(len(self.table._row_widgets), 3)
        self.assertEqual(self.table._row_widgets[-1][0].cget("text"), "10003")
        self.assertEqual(self.table._page_status.get(), "Questions 10001-10003 of 10003 | Page 401 of 401")
        self.assertTrue(self.table._next_button.instate(["disabled"]))
        self.table._change_page(1)
        self.assertEqual(len(self.table._row_widgets), 3)

    def test_empty_short_exact_page_and_replacement_collections(self):
        for count in (0, 1, 25, 26, 50):
            with self.subTest(count=count):
                self.table.set_questions([self.question] * count)
                self.assertEqual(self.table._page, 0)
                self.assertIsNone(self.table._selected_index)
                self.assertEqual(len(self.table._row_widgets), min(count, 25))
                self.assertTrue(self.table._previous_button.instate(["disabled"]))
                self.assertEqual(self.table._next_button.instate(["disabled"]), count <= 25)
                if count:
                    self.assertEqual(self.table._row_widgets[0][3].cget("background"), "#ffe024")
                    self.table.select(count - 1)
                    self.assertTrue(self.table._next_button.instate(["disabled"]))
                else:
                    self.table.select(0)
                    self.assertEqual(self.table._page_status.get(), "No questions loaded")

    def test_master_csv_loads_and_reloading_resets_browsing(self):
        app = TriviaCountdownApp(self.root)
        master = Path(__file__).resolve().parents[1] / "sample_objects" / "master_trivia.csv"
        app.trivia_path.set(str(master))
        app._questions_changed()
        self.assertGreater(len(app._questions), 800)
        self.assertEqual(len(app.question_table._row_widgets), 25)
        app.question_table.select(51)
        self.assertEqual(app._selected_question, 51)
        self.assertEqual(app.question_status.get(), "Preview updated to show question 52.")
        app._questions_changed()
        self.assertEqual(app._selected_question, 0)
        self.assertEqual(app.question_table._page, 0)

    def test_file_dialog_paths_use_native_separators(self):
        app = TriviaCountdownApp(self.root)
        prefix = "C:/Trivia's Files/日本語" if os.name == "nt" else "/tmp/Trivia's Files/日本語"
        with patch.object(app, "_start_preview"), patch.object(app, "_questions_changed"):
            for chooser, dialog, variable, suffix in (
                (app._choose_video, "askopenfilename", app.video_path, "source.mp4"),
                (app._choose_trivia, "askopenfilename", app.trivia_path, "trivia.csv"),
                (app._choose_output, "asksaveasfilename", app.output_path, "output.mp4"),
                (app._choose_overlay_directory, "askdirectory", app.overlay_directory, "overlays"),
            ):
                path = f"{prefix}/{suffix}"
                with self.subTest(dialog=dialog, suffix=suffix), patch(
                    f"trivia_countdown.gui.filedialog.{dialog}", return_value=path
                ):
                    chooser()
                    self.assertEqual(variable.get(), os.path.normpath(path))
                with patch(f"trivia_countdown.gui.filedialog.{dialog}", return_value=""):
                    chooser()
                    self.assertEqual(variable.get(), os.path.normpath(path))
            app.video_path.set(f"{prefix}/pasted.mp4")
            command = app._build_cli_command()
            self.assertIn(quote_cli_argument(os.path.normpath(f"{prefix}/pasted.mp4")), command)
            self.assertEqual(str(app._render_options().overlay_dir), os.path.normpath(f"{prefix}/overlays"))

    @unittest.skipUnless(os.name == "nt", "Windows path display")
    def test_windows_network_paths_keep_their_network_prefix(self):
        app = TriviaCountdownApp(self.root)
        with patch.object(app, "_start_preview"), patch(
            "trivia_countdown.gui.filedialog.askopenfilename", return_value="//server/share/Trivia's/source.mp4"
        ):
            app._choose_video()
        self.assertEqual(app.video_path.get(), r"\\server\share\Trivia's\source.mp4")
        self.assertEqual(app.output_path.get(), r"\\server\share\Trivia's\source_trivia_countdown.mp4")


if __name__ == "__main__":
    unittest.main()
