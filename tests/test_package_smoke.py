"""Package verification must detect failed renders, not just successful startup."""

import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from trivia_countdown.package_smoke import _render_case, _validate_output, run_package_smoke_test


class PackageSmokeTests(unittest.TestCase):
    def metadata(self, *, with_audio=False, duration="3.0"):
        streams = [{"codec_type": "video", "codec_name": "h264", "width": 640, "height": 360}]
        if with_audio:
            streams.append({"codec_type": "audio", "codec_name": "aac"})
        return {"streams": streams, "format": {"duration": duration}}

    def test_output_checks_codecs_dimensions_duration_and_audio(self):
        for with_audio in (False, True):
            _validate_output(self.metadata(with_audio=with_audio), with_audio=with_audio)
            with self.assertRaises(RuntimeError):
                _validate_output(self.metadata(with_audio=not with_audio), with_audio=with_audio)
        for duration in ("0", "4", "nan", "inf"):
            with self.subTest(duration=duration), self.assertRaises(RuntimeError):
                _validate_output(self.metadata(duration=duration), with_audio=False)
        for field, value in (("codec_name", "hevc"), ("width", 320), ("height", 240)):
            metadata = self.metadata()
            metadata["streams"][0][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                _validate_output(metadata, with_audio=False)
        metadata = self.metadata(with_audio=True)
        metadata["streams"][1]["codec_name"] = "mp3"
        with self.assertRaises(RuntimeError):
            _validate_output(metadata, with_audio=True)

    def test_report_requires_a_frozen_application(self):
        with TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            with patch("trivia_countdown.package_smoke.is_frozen", return_value=False):
                self.assertEqual(run_package_smoke_test(report), 1)
            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "failed")
            self.assertIn("frozen application", result["error"])

    def test_success_and_failure_reports_clean_up_test_videos(self):
        for failure in (False, True):
            with self.subTest(failure=failure), TemporaryDirectory() as directory:
                report = Path(directory) / "report.json"
                case_directories = []

                def render_case(path, *, with_audio):
                    case_directories.append(path)
                    (path / "test.mp4").write_bytes(b"temporary video")
                    if failure:
                        raise RuntimeError("Simulated render failure")
                    return {"with_audio": with_audio}

                with patch("trivia_countdown.package_smoke.is_frozen", return_value=True), patch(
                    "trivia_countdown.package_smoke.executable_path", return_value=Path("bundled-tool")
                ), patch("trivia_countdown.package_smoke._run_tool", return_value="tool version"), patch(
                    "trivia_countdown.package_smoke._render_case", side_effect=render_case
                ):
                    self.assertEqual(run_package_smoke_test(report), 1 if failure else 0)
                result = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual(result["status"], "failed" if failure else "passed")
                self.assertTrue(case_directories)
                self.assertTrue(all(not path.exists() for path in case_directories))
                if failure:
                    self.assertIn("Simulated render failure", result["error"])
                else:
                    self.assertEqual(result["cases"], [{"with_audio": False}, {"with_audio": True}])

    def test_gui_render_smoke_returns_failure_and_destroys_window(self):
        from trivia_countdown.gui import main

        root = Mock()
        report_path = Path("report.json").resolve()
        with patch.dict("os.environ", {
            "TRIVIA_COUNTDOWN_SMOKE_TEST": "render",
            "TRIVIA_COUNTDOWN_SMOKE_REPORT": str(report_path),
        }), patch("trivia_countdown.gui.tk.Tk", return_value=root), patch(
            "trivia_countdown.gui.TriviaCountdownApp"
        ), patch("trivia_countdown.package_smoke.run_package_smoke_test", return_value=1) as smoke:
            self.assertEqual(main(), 1)
        smoke.assert_called_once_with(report_path)
        root.destroy.assert_called_once()
        root.mainloop.assert_not_called()

    def test_gui_startup_smoke_stays_lightweight_and_render_requires_report(self):
        from trivia_countdown.gui import main

        for mode, report, expected in (("1", "", 0), ("render", "", 1), ("render", "relative.json", 1)):
            root = Mock()
            with self.subTest(mode=mode, report=report), patch.dict("os.environ", {
                "TRIVIA_COUNTDOWN_SMOKE_TEST": mode,
                "TRIVIA_COUNTDOWN_SMOKE_REPORT": report,
            }), patch("trivia_countdown.gui.tk.Tk", return_value=root), patch(
                "trivia_countdown.gui.TriviaCountdownApp"
            ), patch("trivia_countdown.package_smoke.run_package_smoke_test") as smoke:
                self.assertEqual(main(), expected)
            smoke.assert_not_called()
            root.destroy.assert_called_once()
            root.mainloop.assert_not_called()

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg tools required")
    def test_real_smoke_render_cases(self):
        with TemporaryDirectory(prefix="package-smoke-caf\u00e9's-") as directory:
            for with_audio in (False, True):
                root = Path(directory) / str(with_audio)
                root.mkdir()
                result = _render_case(root, with_audio=with_audio)
                self.assertEqual(result["with_audio"], with_audio)
                self.assertGreater(result["bytes"], 0)


if __name__ == "__main__":
    unittest.main()
