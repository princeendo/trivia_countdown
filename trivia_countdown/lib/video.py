"""Video probing and ffmpeg composition helpers."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Optional

from PIL import Image

from .models import RenderedOverlay, VideoDimensions


def require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required executable not found: {name}")


def validate_input_paths(video_file: Path, trivia_file: Path) -> None:
    if not video_file.is_file():
        raise ValueError(f"Video file does not exist: {video_file}")
    if not trivia_file.is_file():
        raise ValueError(f"Trivia CSV does not exist: {trivia_file}")


def get_video_dimensions(video_file: Path) -> VideoDimensions:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(video_file),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or "ffprobe failed to inspect the input video"
        raise RuntimeError(message)

    try:
        streams = json.loads(result.stdout).get("streams", [])
        width = int(streams[0]["width"])
        height = int(streams[0]["height"])
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("Could not determine input video dimensions") from exc

    if width <= 0 or height <= 0:
        raise RuntimeError("Input video dimensions must be greater than zero")
    return VideoDimensions(width=width, height=height)


def get_video_duration(video_file: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_file),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or "ffprobe failed to inspect the input video duration"
        raise RuntimeError(message)

    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("Could not determine input video duration") from exc

    if duration <= 0:
        raise RuntimeError("Input video duration must be greater than zero")
    return duration


def parse_frame_rate(value: object) -> Optional[float]:
    if not isinstance(value, str) or not value:
        return None
    try:
        if "/" in value:
            numerator_text, denominator_text = value.split("/", 1)
            denominator = float(denominator_text)
            if denominator == 0:
                return None
            frame_rate = float(numerator_text) / denominator
        else:
            frame_rate = float(value)
    except ValueError:
        return None

    if not math.isfinite(frame_rate) or frame_rate <= 0:
        return None
    return frame_rate


def get_video_fps(video_file: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate,r_frame_rate",
        "-of",
        "json",
        str(video_file),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or "ffprobe failed to inspect the input video FPS"
        raise RuntimeError(message)

    try:
        stream = json.loads(result.stdout).get("streams", [])[0]
    except (IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Could not determine input video FPS") from exc

    for key in ("avg_frame_rate", "r_frame_rate"):
        frame_rate = parse_frame_rate(stream.get(key))
        if frame_rate is not None:
            return frame_rate

    raise RuntimeError("Could not determine input video FPS")


def parse_ffmpeg_time(value: str) -> Optional[float]:
    parts = value.split(":")
    if len(parts) != 3:
        return None
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
    except ValueError:
        return None
    return hours * 3600 + minutes * 60 + seconds


def quote_ffconcat_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace("'", "\\'")


def build_overlay_schedule(
    overlay_paths: list[RenderedOverlay],
    *,
    blank_overlay_path: Path,
    question_duration: float,
    answer_duration: float,
    answer_flash_duration: float,
    answer_flash_interval: float,
    start_delay: float,
    video_duration: float,
) -> list[tuple[Path, float]]:
    schedule: list[tuple[Path, float]] = []
    elapsed = 0.0

    def add_overlay_window(path: Path, duration: float) -> None:
        nonlocal elapsed
        if duration <= 0:
            return
        schedule.append((path, duration))
        elapsed += duration

    if start_delay > 0:
        add_overlay_window(blank_overlay_path, start_delay)

    for overlay in overlay_paths:
        add_overlay_window(overlay.normal_path, question_duration)

        transition_duration = sum(frame.duration for frame in overlay.transition_frames)
        answer_display_duration = max(0.0, answer_duration - transition_duration)

        flash_end = min(answer_flash_duration, answer_display_duration)
        flash_enabled = answer_flash_duration > 0 and answer_flash_interval > 0
        if flash_enabled and flash_end > 0:
            flash_window_duration = flash_end
            flash_chunk_count = max(1, int(flash_window_duration // answer_flash_interval))
            flash_chunk_duration = flash_window_duration / flash_chunk_count
            flash_start_time = 0.0
            chunk_index = 0

            while flash_start_time < flash_end:
                chunk_end_time = min(flash_start_time + flash_chunk_duration, flash_end)
                use_reveal_overlay = chunk_index % 2 == 1 or chunk_end_time >= answer_display_duration
                add_overlay_window(
                    overlay.reveal_path if use_reveal_overlay else overlay.normal_path,
                    chunk_end_time - flash_start_time,
                )
                flash_start_time = chunk_end_time
                chunk_index += 1
        else:
            flash_end = 0.0

        add_overlay_window(overlay.reveal_path, answer_display_duration - flash_end)
        for frame in overlay.transition_frames:
            add_overlay_window(frame.path, frame.duration)

    if elapsed < video_duration:
        add_overlay_window(blank_overlay_path, video_duration - elapsed)

    return schedule


def write_overlay_concat_file(schedule: list[tuple[Path, float]], concat_file: Path) -> None:
    lines = ["ffconcat version 1.0"]
    for path, duration in schedule:
        lines.append(f"file '{quote_ffconcat_path(path)}'")
        lines.append(f"duration {duration:.6f}")
    if schedule:
        lines.append(f"file '{quote_ffconcat_path(schedule[-1][0])}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_filter_graph(
    *,
    video_fps: float,
    fade_in_start: float,
    fade_in_duration: float,
    fade_out_start: float,
    fade_out_duration: float,
) -> str:
    overlay_filters = ["setpts=PTS-STARTPTS", "format=rgba"]
    if fade_in_duration > 0 or fade_out_duration > 0:
        overlay_filters.append(f"fps=fps={video_fps:.6f}:start_time=0")
    if fade_in_duration > 0:
        overlay_filters.append(
            f"fade=t=in:st={fade_in_start:.6f}:d={fade_in_duration:.6f}:alpha=1"
        )
    if fade_out_duration > 0:
        overlay_filters.append(
            f"fade=t=out:st={fade_out_start:.6f}:d={fade_out_duration:.6f}:alpha=1"
        )

    filters = [
        "[0:v]format=rgba[base]",
        f"[1:v]{','.join(overlay_filters)}[overlay]",
        "[base][overlay]overlay=0:0:format=auto:eof_action=pass,format=yuv420p[vout]",
    ]

    return ";".join(filters)


def compose_video(
    video_file: Path,
    output_file: Path,
    overlay_paths: list[RenderedOverlay],
    dimensions: VideoDimensions,
    *,
    video_duration: float,
    video_fps: float,
    question_duration: float,
    answer_duration: float,
    answer_flash_duration: float,
    answer_flash_interval: float,
    start_delay: float,
    fade_in_time: float,
    fade_out_time: float,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    trivia_overlay_duration = len(overlay_paths) * (question_duration + answer_duration)
    trivia_end = start_delay + trivia_overlay_duration
    fade_in_duration = min(fade_in_time, trivia_overlay_duration)
    fade_out_duration = min(fade_out_time, trivia_overlay_duration)
    fade_out_start = trivia_end - fade_out_duration

    with TemporaryDirectory(prefix="trivia_countdown_compose_") as compose_directory:
        compose_directory_path = Path(compose_directory)
        blank_overlay_path = compose_directory_path / "blank_overlay.png"
        Image.new(
            "RGBA",
            (dimensions.width, dimensions.height),
            (0, 0, 0, 0),
        ).save(blank_overlay_path)
        concat_file = compose_directory_path / "overlay_timeline.ffconcat"
        write_overlay_concat_file(
            build_overlay_schedule(
                overlay_paths,
                blank_overlay_path=blank_overlay_path,
                question_duration=question_duration,
                answer_duration=answer_duration,
                answer_flash_duration=answer_flash_duration,
                answer_flash_interval=answer_flash_interval,
                start_delay=start_delay,
                video_duration=video_duration,
            ),
            concat_file,
        )

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_file),
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
        ]

        command.extend(
            [
                "-filter_complex",
                build_filter_graph(
                    video_fps=video_fps,
                    fade_in_start=start_delay,
                    fade_in_duration=fade_in_duration,
                    fade_out_start=fade_out_start,
                    fade_out_duration=fade_out_duration,
                ),
                "-map",
                "[vout]",
                "-map",
                "0:a?",
                "-map_metadata",
                "0",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-t",
                f"{video_duration:.3f}",
                "-progress",
                "pipe:1",
                "-nostats",
                "-movflags",
                "+faststart",
                str(output_file),
            ]
        )

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stderr_lines: list[str] = []

        def collect_stderr() -> None:
            assert process.stderr is not None
            for line in process.stderr:
                stderr_lines.append(line)

        stderr_thread = threading.Thread(target=collect_stderr, daemon=True)
        stderr_thread.start()

        assert process.stdout is not None
        last_reported_seconds = -1.0
        for raw_line in process.stdout:
            line = raw_line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            encoded_seconds: Optional[float] = None
            if key in {"out_time_ms", "out_time_us"}:
                try:
                    encoded_seconds = int(value) / 1_000_000
                except ValueError:
                    encoded_seconds = None
            elif key == "out_time":
                encoded_seconds = parse_ffmpeg_time(value)

            if (
                encoded_seconds is not None
                and progress_callback
                and encoded_seconds > last_reported_seconds
            ):
                last_reported_seconds = encoded_seconds
                progress_callback(min(video_duration, encoded_seconds))

        return_code = process.wait()
        stderr_thread.join()
        if return_code != 0:
            message = (
                "".join(stderr_lines).strip()
                or "ffmpeg failed while composing the output video"
            )
            raise RuntimeError(message)
