"""Opt-in frozen-application render checks used by Windows package verification."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import subprocess
from tempfile import TemporaryDirectory
import traceback

from .app import RenderOptions, RenderRequest, prepare_render, run_render
from .lib.video import extract_video_still, windows_subprocess_kwargs
from .resources import executable_path, is_frozen, windows_package_full_name


def _run_tool(name: str, *arguments: str) -> str:
    result = subprocess.run(
        [str(executable_path(name)), *arguments],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        **windows_subprocess_kwargs(),
    )
    if result.returncode:
        raise RuntimeError(f"{name} exited with {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def _validate_output(metadata: dict, *, with_audio: bool) -> None:
    streams = metadata.get("streams", [])
    video = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if len(video) != 1 or (
        video[0].get("codec_name"), video[0].get("width"), video[0].get("height")
    ) != ("h264", 640, 360):
        raise RuntimeError(f"Expected one 640x360 H.264 video stream: {streams}")
    if (with_audio and (len(audio) != 1 or audio[0].get("codec_name") != "aac")) or (
        not with_audio and audio
    ):
        raise RuntimeError(f"Unexpected audio streams: {audio}")
    duration = float(metadata["format"]["duration"])
    if not math.isfinite(duration) or abs(duration - 3.0) > 0.15:
        raise RuntimeError(f"Expected a three-second output, received {duration}")


def _render_case(directory: Path, *, with_audio: bool) -> dict:
    source = directory / "source video's.mp4"
    output = directory / "finished video's.mp4"
    trivia = directory / "questions.csv"
    trivia.write_text(
        "question,answer_1,answer_2,answer_3,answer_4,correct_answer\n"
        "Which planet is the Red Planet?,Venus,Mars,Jupiter,Saturn,2\n",
        encoding="utf-8",
    )
    arguments = ["-v", "error", "-f", "lavfi", "-i", "color=c=navy:s=640x360:r=24"]
    if with_audio:
        arguments += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000"]
    arguments += ["-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if with_audio:
        arguments += ["-c:a", "aac"]
    _run_tool("ffmpeg", *arguments, str(source))
    with extract_video_still(source, 0.5) as frame:
        if frame.size != (640, 360):
            raise RuntimeError(f"Unexpected preview dimensions: {frame.size}")
    result = run_render(prepare_render(RenderRequest(
        source,
        trivia,
        output,
        RenderOptions(
            question_duration=1,
            answer_duration=1,
            answer_flash_duration=0.4,
            answer_flash_interval=0.2,
            start_delay=0,
            end_early=0,
            fade_in_time=0.2,
            fade_out_time=0.2,
        ),
    )))
    if result.overlay_count < 2 or not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("The packaged render did not create a nonempty one-question video")
    metadata = json.loads(_run_tool(
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output),
    ))
    _validate_output(metadata, with_audio=with_audio)
    # Decode every output frame, not just its container headers.
    _run_tool("ffmpeg", "-v", "error", "-xerror", "-i", str(output), "-f", "null", "-")
    return {"with_audio": with_audio, "bytes": output.stat().st_size, "metadata": metadata}


def run_package_smoke_test(report_path: Path) -> int:
    """Write machine-readable results even when a frozen render check fails."""
    report = {
        "status": "failed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "frozen": is_frozen(),
        "cases": [],
    }
    try:
        if not is_frozen():
            raise RuntimeError("Package verification must run from the frozen application")
        report["windows_package_full_name"] = windows_package_full_name()
        report["tools"] = {
            name: {"path": str(executable_path(name)), "version": _run_tool(name, "-version")}
            for name in ("ffmpeg", "ffprobe")
        }
        with TemporaryDirectory(prefix="package-smoke-caf\u00e9's-", dir=report_path.parent) as temporary:
            for with_audio in (False, True):
                directory = Path(temporary) / ("with audio" if with_audio else "without audio")
                directory.mkdir()
                report["cases"].append(_render_case(directory, with_audio=with_audio))
        report["status"] = "passed"
    except Exception:
        report["error"] = traceback.format_exc()
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["status"] == "passed" else 1
