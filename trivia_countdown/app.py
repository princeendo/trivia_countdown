"""Shared application services for command-line and desktop interfaces."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Callable, Optional

from .lib.cancellation import CancellationToken
from .lib.models import RenderTimings, TriviaQuestion, VideoDimensions
from .lib.pipeline import render_and_compose
from .lib.trivia import load_trivia, max_full_questions_for_video, order_questions
from .lib.video import (
    get_video_dimensions,
    get_video_duration,
    get_video_fps,
    require_executable,
    validate_input_paths,
)


@dataclass(frozen=True)
class RenderOptions:
    randomize: bool = False
    seed: Optional[int] = None
    question_duration: float = 10.0
    answer_duration: float = 2.5
    answer_flash_duration: float = 1.5
    answer_flash_interval: float = 0.2
    start_delay: float = 10.0
    end_early: float = 15.0
    fade_in_time: float = 0.5
    fade_out_time: float = 0.5
    mid_question_fade: float = 0.3
    overlay_dir: Optional[Path] = None


@dataclass(frozen=True)
class RenderRequest:
    video_file: Path
    trivia_file: Path
    output_file: Path
    options: RenderOptions


@dataclass(frozen=True)
class VideoInfo:
    dimensions: VideoDimensions
    duration: float
    fps: float


@dataclass(frozen=True)
class PreparedRender:
    request: RenderRequest
    video: VideoInfo
    questions: tuple[TriviaQuestion, ...]
    validated_question_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ProgressEvent:
    phase: str
    fraction: float
    detail: str


@dataclass(frozen=True)
class RenderResult:
    overlay_count: int
    persisted_overlay_dir: Optional[Path]
    timings: RenderTimings


ProgressCallback = Callable[[ProgressEvent], None]


def default_output_path(video_file: Path) -> Path:
    return video_file.with_name(f"{video_file.stem}_trivia_countdown.mp4")


def _validate_finite(value: float, name: str, *, positive: bool) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if positive and value <= 0:
        raise ValueError(f"{name} must be greater than 0")
    if not positive and value < 0:
        raise ValueError(f"{name} must be greater than or equal to 0")


def validate_options(options: RenderOptions) -> None:
    _validate_finite(options.question_duration, "Question duration", positive=True)
    _validate_finite(options.answer_duration, "Answer duration", positive=True)
    for value, name in (
        (options.answer_flash_duration, "Answer flash duration"),
        (options.answer_flash_interval, "Answer flash interval"),
        (options.start_delay, "Start delay"),
        (options.end_early, "End early"),
        (options.fade_in_time, "Fade in time"),
        (options.fade_out_time, "Fade out time"),
        (options.mid_question_fade, "Mid-question fade"),
    ):
        _validate_finite(value, name, positive=False)
    if options.answer_flash_duration > options.answer_duration:
        raise ValueError("Answer flash duration cannot exceed answer duration")
    if options.mid_question_fade > options.answer_duration:
        raise ValueError("Mid-question fade cannot exceed answer duration")


def load_questions(trivia_file: Path, options: RenderOptions) -> list[TriviaQuestion]:
    validate_options(options)
    return order_questions(load_trivia(trivia_file), randomize=options.randomize, seed=options.seed)


def prepare_render(request: RenderRequest) -> PreparedRender:
    validate_options(request.options)
    validate_input_paths(request.video_file, request.trivia_file)
    if request.video_file.resolve() == request.output_file.resolve():
        raise ValueError("Output video must be different from the input video")
    require_executable("ffmpeg")
    require_executable("ffprobe")

    video = VideoInfo(
        dimensions=get_video_dimensions(request.video_file),
        duration=get_video_duration(request.video_file),
        fps=get_video_fps(request.video_file),
    )
    questions = load_questions(request.trivia_file, request.options)
    max_questions = max_full_questions_for_video(
        video.duration,
        request.options.question_duration,
        request.options.answer_duration,
        start_delay=request.options.start_delay,
        end_early=request.options.end_early,
    )
    if max_questions <= 0:
        raise ValueError("Input video is too short to show even one full trivia question")

    warnings: list[str] = []
    if request.options.question_duration < 1.0:
        warnings.append("Question duration is less than 1.0s and may be hard to read.")
    if request.options.answer_duration < 1.0:
        warnings.append("Answer highlight duration is less than 1.0s and may be hard to notice.")
    return PreparedRender(
        request=request,
        video=video,
        questions=tuple(questions[:max_questions]),
        validated_question_count=len(questions),
        warnings=tuple(warnings),
    )


def run_render(
    prepared: PreparedRender,
    *,
    progress_callback: Optional[ProgressCallback] = None,
    cancellation_token: Optional[CancellationToken] = None,
) -> RenderResult:
    def report(phase: str, fraction: float, detail: str) -> None:
        if progress_callback:
            progress_callback(ProgressEvent(phase, fraction, detail))

    overlay_count, persisted_overlay_dir, timings = render_and_compose(
        prepared.request.video_file,
        prepared.request.output_file,
        list(prepared.questions),
        prepared.video.dimensions,
        video_duration=prepared.video.duration,
        video_fps=prepared.video.fps,
        question_duration=prepared.request.options.question_duration,
        answer_duration=prepared.request.options.answer_duration,
        answer_flash_duration=prepared.request.options.answer_flash_duration,
        answer_flash_interval=prepared.request.options.answer_flash_interval,
        start_delay=prepared.request.options.start_delay,
        fade_in_time=prepared.request.options.fade_in_time,
        fade_out_time=prepared.request.options.fade_out_time,
        mid_question_fade=prepared.request.options.mid_question_fade,
        overlay_dir=prepared.request.options.overlay_dir,
        progress_callback=report,
        cancel_check=cancellation_token.cancelled if cancellation_token else None,
    )
    return RenderResult(overlay_count, persisted_overlay_dir, timings)
