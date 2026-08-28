"""Focused tests for the shared render service and preview primitives."""

from __future__ import annotations

import math
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest

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
from trivia_countdown.lib.overlays import build_panel_layout, render_question_image, render_overlays
from trivia_countdown.lib.video import extract_video_still


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
