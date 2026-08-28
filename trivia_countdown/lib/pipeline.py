"""End-to-end render and composition orchestration."""

from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Optional

from .cancellation import check_cancelled
from .models import RenderTimings, TriviaQuestion, VideoDimensions
from .overlays import render_overlays
from .video import compose_video


def render_and_compose(
    video_file: Path,
    output_file: Path,
    questions: list[TriviaQuestion],
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
    mid_question_fade: float,
    overlay_dir: Optional[Path],
    progress_callback: Optional[Callable[[str, float, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> tuple[int, Optional[Path], RenderTimings]:
    overlay_start = time.monotonic()

    def report_overlay_progress(completed: int, total: int) -> None:
        if progress_callback and total > 0:
            progress_callback("Rendering overlays", completed / total, f"{completed}/{total}")

    def report_compose_progress(encoded_seconds: float) -> None:
        if progress_callback:
            fraction = encoded_seconds / video_duration if video_duration > 0 else 0.0
            progress_callback("Composing video", fraction, f"{encoded_seconds:.1f}s/{video_duration:.1f}s")

    if overlay_dir:
        overlay_paths = render_overlays(
            questions,
            dimensions,
            overlay_dir,
            mid_question_fade,
            video_fps,
            report_overlay_progress,
            cancel_check,
        )
        overlay_seconds = time.monotonic() - overlay_start

        compose_start = time.monotonic()
        compose_video(
            video_file,
            output_file,
            overlay_paths,
            dimensions,
            video_duration=video_duration,
            video_fps=video_fps,
            question_duration=question_duration,
            answer_duration=answer_duration,
            answer_flash_duration=answer_flash_duration,
            answer_flash_interval=answer_flash_interval,
            start_delay=start_delay,
            fade_in_time=fade_in_time,
            fade_out_time=fade_out_time,
            progress_callback=report_compose_progress,
            cancel_check=cancel_check,
        )
        if progress_callback:
            progress_callback("Composing video", 1.0, "Complete")
        compose_seconds = time.monotonic() - compose_start
        overlay_count = sum(2 + len(overlay.transition_frames) for overlay in overlay_paths)
        return overlay_count, overlay_dir, RenderTimings(overlay_seconds, compose_seconds)

    with TemporaryDirectory(prefix="trivia_countdown_") as temporary_directory:
        check_cancelled(cancel_check)
        overlay_paths = render_overlays(
            questions,
            dimensions,
            Path(temporary_directory),
            mid_question_fade,
            video_fps,
            report_overlay_progress,
            cancel_check,
        )
        overlay_seconds = time.monotonic() - overlay_start

        compose_start = time.monotonic()
        compose_video(
            video_file,
            output_file,
            overlay_paths,
            dimensions,
            video_duration=video_duration,
            video_fps=video_fps,
            question_duration=question_duration,
            answer_duration=answer_duration,
            answer_flash_duration=answer_flash_duration,
            answer_flash_interval=answer_flash_interval,
            start_delay=start_delay,
            fade_in_time=fade_in_time,
            fade_out_time=fade_out_time,
            progress_callback=report_compose_progress,
            cancel_check=cancel_check,
        )
        if progress_callback:
            progress_callback("Composing video", 1.0, "Complete")
        compose_seconds = time.monotonic() - compose_start
        overlay_count = sum(2 + len(overlay.transition_frames) for overlay in overlay_paths)
        return overlay_count, None, RenderTimings(overlay_seconds, compose_seconds)
