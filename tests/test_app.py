"""Focused tests for the shared render service and preview primitives."""

from __future__ import annotations

import io
import math
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest
from unittest.mock import patch

from PIL import Image

from trivia_countdown.app import (
    RenderOptions,
    RenderRequest,
    default_output_path,
    load_questions,
    prepare_render,
    run_render,
    validate_options,
)
from trivia_countdown.lib.cancellation import CancellationToken, RenderCancelled
from trivia_countdown.lib.models import TriviaQuestion, VideoDimensions
from trivia_countdown.lib.overlays import build_panel_layout, load_font, render_question_image, render_overlays
from trivia_countdown.lib.progress import ProgressReporter
from trivia_countdown.lib.video import (
    extract_video_still,
    quote_ffconcat_path,
    windows_subprocess_kwargs,
    write_overlay_concat_file,
)
from trivia_countdown.resources import executable_path, resource_path


class GuiSmokeTests(unittest.TestCase):
    def test_gui_constructs_when_a_tk_display_is_available(self) -> None:
        from trivia_countdown.gui import TriviaCountdownApp

        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        try:
            root.withdraw()
            app = TriviaCountdownApp(root)
            app.video_path.set("/tmp/source video.mp4")
            app.trivia_path.set("/tmp/trivia.csv")
            command_with_defaults = app._build_cli_command()
            self.assertIn("--duration 10", command_with_defaults)
            self.assertIn("'/tmp/source video.mp4'", command_with_defaults)
            app.include_default_parameters.set(False)
            self.assertNotIn("--duration 10", app._build_cli_command())

            question = TriviaQuestion("Question", ("One", "Two", "Three", "Four"), 2)
            app.question_table.set_questions([question])
            app.question_table.select(0)
            self.assertEqual(app.question_status.get(), "Preview updated to show question 1.")
            self.assertEqual(app.question_table._row_widgets[0][0].cget("background"), "#d9f2df")
        finally:
            root.destroy()

    def test_powershell_command_escapes_apostrophes(self) -> None:
        from trivia_countdown.gui import quote_cli_argument

        with patch("trivia_countdown.gui.sys.platform", "win32"):
            self.assertEqual(
                quote_cli_argument(r"C:\Trivia's\source video.mp4"),
                "'C:\\Trivia''s\\source video.mp4'",
            )


CSV_CONTENT = """question,answer_1,answer_2,answer_3,answer_4,correct_answer
Which planet is known as the Red Planet?,Venus,Mars,Jupiter,Saturn,2
Which element has the symbol O?,Gold,Oxygen,Silver,Iron,2
"""


class RenderServiceTests(unittest.TestCase):
    def write_csv(self, directory: Path) -> Path:
        path = directory / "trivia.csv"
        path.write_text(CSV_CONTENT, encoding="utf-8")
        return path

    def test_default_output_path(self) -> None:
        self.assertEqual(
            default_output_path(Path("/tmp/countdown.mov")),
            Path("/tmp/countdown_trivia_countdown.mp4"),
        )

    def test_source_resource_path_finds_app_icon(self) -> None:
        icon_path = resource_path("assets", "app_icon.png")
        self.assertTrue(icon_path.is_file())
        with Image.open(icon_path) as icon:
            self.assertEqual(icon.mode, "RGBA")
            self.assertEqual(icon.getpixel((0, 0))[3], 0)

    def test_frozen_executable_path_uses_bundled_binary(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "bin" / "ffmpeg"
            binary.parent.mkdir()
            binary.touch()
            with patch("trivia_countdown.resources.sys.frozen", True, create=True), patch(
                "trivia_countdown.resources.sys._MEIPASS", str(root), create=True
            ):
                self.assertEqual(executable_path("ffmpeg"), binary)

    def test_frozen_windows_executable_path_uses_exe_suffix(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "bin" / "ffmpeg.exe"
            binary.parent.mkdir()
            binary.touch()
            with patch("trivia_countdown.resources.sys.frozen", True, create=True), patch(
                "trivia_countdown.resources.sys._MEIPASS", str(root), create=True
            ), patch("trivia_countdown.resources.sys.platform", "win32"):
                self.assertEqual(executable_path("ffmpeg"), binary)

    def test_bundled_fonts_load_at_requested_sizes(self) -> None:
        regular = load_font(18)
        bold = load_font(34, bold=True)
        self.assertEqual(regular.size, 18)
        self.assertEqual(bold.size, 34)

    def test_concat_manifest_uses_absolute_escaped_paths(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            overlay = root / "relative overlays" / "question's.png"
            concat_file = root / "timeline.ffconcat"
            write_overlay_concat_file([(overlay, 1.25)], concat_file)
            escaped_path = quote_ffconcat_path(overlay.resolve())
            self.assertEqual(
                concat_file.read_text(encoding="utf-8"),
                f"ffconcat version 1.0\nfile '{escaped_path}'\nduration 1.250000\nfile '{escaped_path}'\n",
            )

    def test_concat_path_uses_ffmpeg_apostrophe_escaping(self) -> None:
        self.assertEqual(
            quote_ffconcat_path(Path("C:/Trivia Files/question's.png")),
            r"C:/Trivia Files/question'\''s.png",
        )

    def test_redirected_progress_uses_newlines_without_ansi(self) -> None:
        output = io.StringIO()
        with patch("trivia_countdown.lib.progress.sys.stderr", output):
            reporter = ProgressReporter(enabled=True)
            reporter.update_fraction("Rendering overlays", 0.5, "1/2", 0.0)
            reporter.complete_phase("Rendering overlays", 0.0)
        self.assertNotIn("\r", output.getvalue())
        self.assertNotIn("\033", output.getvalue())
        self.assertEqual(len(output.getvalue().splitlines()), 2)

    def test_frozen_windows_processes_hide_child_consoles(self) -> None:
        with patch("trivia_countdown.lib.video.os.name", "nt"), patch(
            "trivia_countdown.lib.video.is_frozen", return_value=True
        ), patch("trivia_countdown.lib.video.subprocess.CREATE_NO_WINDOW", 0x08000000, create=True):
            self.assertEqual(windows_subprocess_kwargs(), {"creationflags": 0x08000000})

    def test_options_reject_nonfinite_and_invalid_cross_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            validate_options(RenderOptions(question_duration=math.nan))
        with self.assertRaisesRegex(ValueError, "flash duration"):
            validate_options(RenderOptions(answer_flash_duration=3.0, answer_duration=2.0))
        with self.assertRaisesRegex(ValueError, "fade"):
            validate_options(RenderOptions(mid_question_fade=3.0, answer_duration=2.0))

    def test_seeded_question_order_is_repeatable(self) -> None:
        with TemporaryDirectory() as directory:
            csv_file = self.write_csv(Path(directory))
            options = RenderOptions(randomize=True, seed=19)
            first_order = load_questions(csv_file, options)
            second_order = load_questions(csv_file, options)
        self.assertEqual(first_order, second_order)

    def test_question_image_marks_only_the_correct_answer(self) -> None:
        dimensions = VideoDimensions(960, 540)
        question = TriviaQuestion("Question", ("One", "Two", "Three", "Four"), 2)
        image = render_question_image(question, dimensions, reveal_answer=True)
        layout = build_panel_layout(dimensions)
        first_box = layout.answer_boxes[0]
        second_box = layout.answer_boxes[1]
        self.assertEqual(image.getpixel((first_box[0] + 12, first_box[1] + 12))[:3], (11, 34, 82))
        self.assertEqual(image.getpixel((second_box[0] + 12, second_box[1] + 12))[:3], (255, 224, 36))

    def test_cancelled_overlay_render_stops_before_writing_images(self) -> None:
        token = CancellationToken()
        token.cancel()
        question = TriviaQuestion("Question", ("One", "Two", "Three", "Four"), 1)
        with TemporaryDirectory() as directory:
            with self.assertRaises(RenderCancelled):
                render_overlays(
                    [question],
                    VideoDimensions(160, 90),
                    Path(directory),
                    mid_question_fade=0,
                    video_fps=30,
                    cancel_check=token.cancelled,
                )


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg and ffprobe are required")
class VideoIntegrationTests(unittest.TestCase):
    def test_preview_and_short_render(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.mp4"
            trivia = root / "trivia.csv"
            output = root / "result.mp4"
            trivia.write_text(CSV_CONTENT, encoding="utf-8")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=blue:s=160x90:d=2",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(source),
                ],
                capture_output=True,
                check=True,
            )
            frame = extract_video_still(source, 0.5)
            self.assertEqual(frame.size, (160, 90))
            request = RenderRequest(
                source,
                trivia,
                output,
                RenderOptions(
                    question_duration=0.5,
                    answer_duration=0.3,
                    answer_flash_duration=0,
                    answer_flash_interval=0,
                    start_delay=0,
                    end_early=0,
                    fade_in_time=0,
                    fade_out_time=0,
                    mid_question_fade=0,
                ),
            )
            prepared = prepare_render(request)
            progress = []
            result = run_render(prepared, progress_callback=progress.append)
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)
            self.assertGreater(result.overlay_count, 0)
            self.assertTrue(any(event.phase == "Composing video" for event in progress))


if __name__ == "__main__":
    unittest.main()
