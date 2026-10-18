"""User-facing failures must remain actionable without Python tracebacks."""

import builtins
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

from trivia_countdown import cli
from trivia_countdown.app import PreparedRender, RenderOptions, RenderRequest, VideoInfo
from trivia_countdown.lib.models import TriviaQuestion, VideoDimensions


class LauncherTests(unittest.TestCase):
    def test_cli_reports_preparation_errors_on_stderr(self):
        for error in (PermissionError("Access denied"), FileNotFoundError("ffprobe missing"), OSError("File locked")):
            with self.subTest(error=error), patch("sys.argv", ["make_trivia_countdown.py", "video.mp4", "trivia.csv"]), patch(
                "trivia_countdown.cli.prepare_render", side_effect=error
            ), redirect_stderr(io.StringIO()) as stderr, redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(cli.main(), 1)
                self.assertEqual(stderr.getvalue(), f"error: {error}\n")
                self.assertEqual(stdout.getvalue(), "")

    def test_cli_reports_render_permission_errors_without_tracebacks(self):
        request = RenderRequest(Path("video.mp4"), Path("trivia.csv"), Path("output.mp4"), RenderOptions())
        prepared = PreparedRender(
            request, VideoInfo(VideoDimensions(640, 360), 60, 24),
            (TriviaQuestion("Question?", ("A", "B", "C", "D"), 1),), 1, (),
        )
        with patch("sys.argv", ["make_trivia_countdown.py", "video.mp4", "trivia.csv"]), patch(
            "trivia_countdown.cli.prepare_render", return_value=prepared
        ), patch("trivia_countdown.cli.run_render", side_effect=PermissionError("Output directory denied")), redirect_stderr(
            io.StringIO()
        ) as stderr, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(), 1)
            self.assertEqual(stderr.getvalue(), "error: Output directory denied\n")

    def test_missing_tkinter_is_reported_but_unrelated_import_errors_are_not_hidden(self):
        launcher = Path(__file__).resolve().parents[1] / "make_trivia_countdown_gui.py"
        original_import = builtins.__import__
        for missing in ("tkinter", "_tkinter", "unrelated_dependency"):
            def import_module(name, *args, **kwargs):
                if name == "trivia_countdown.gui":
                    raise ModuleNotFoundError(f"No module named {missing!r}", name=missing)
                return original_import(name, *args, **kwargs)

            with self.subTest(missing=missing), patch("builtins.__import__", side_effect=import_module), redirect_stderr(
                io.StringIO()
            ) as stderr:
                if missing == "unrelated_dependency":
                    with self.assertRaises(ModuleNotFoundError):
                        runpy.run_path(str(launcher), run_name="__main__")
                    self.assertEqual(stderr.getvalue(), "")
                else:
                    with self.assertRaises(SystemExit) as raised:
                        runpy.run_path(str(launcher), run_name="__main__")
                    self.assertEqual(raised.exception.code, 1)
                    self.assertIn("Tkinter is unavailable", stderr.getvalue())
                    self.assertIn("Tcl/Tk support", stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
