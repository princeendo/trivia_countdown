"""Command-line interface for trivia countdown video generation."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .lib.pipeline import render_and_compose
from .lib.progress import ProgressReporter, format_duration, format_seconds
from .lib.trivia import load_trivia, max_full_questions_for_video, order_questions
from .lib.video import (
    get_video_dimensions,
    get_video_duration,
    get_video_fps,
    require_executable,
    validate_input_paths,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Overlay trivia question panels onto a countdown video.",
    )
    parser.add_argument("video_file", type=Path, help="Input video file, such as mp4, mkv, or avi.")
    parser.add_argument("trivia_file", type=Path, help="CSV file containing trivia questions.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output MP4 path. Defaults to <input_stem>_trivia_countdown.mp4 next to the input video.",
    )
    parser.add_argument(
        "--random",
        action="store_true",
        dest="randomize",
        help="Randomize the order of questions.",
    )
    parser.add_argument("--seed", type=int, help="Seed for repeatable randomized question order.")
    parser.add_argument(
        "--duration",
        type=positive_float,
        default=10.0,
        help="Seconds to show each question before revealing the answer. Accepts decimals. Default: 10.",
    )
    parser.add_argument(
        "--answer-duration",
        type=positive_float,
        default=2.5,
        help="Approximate seconds to highlight the correct answer. Accepts decimals. Default: 2.5.",
    )
    parser.add_argument(
        "--answer-flash-duration",
        type=nonnegative_float,
        default=1.5,
        help=(
            "Seconds for the answer to alternate between normal and highlighted before staying solid. "
            "Accepts decimals. Use 0 to disable blinking. Default: 1.5."
        ),
    )
    parser.add_argument(
        "--answer-flash-interval",
        type=nonnegative_float,
        default=0.2,
        help=(
            "Seconds between answer flash state changes. Accepts decimals. "
            "Use 0 to disable blinking. Default: 0.2."
        ),
    )
    parser.add_argument(
        "--start-delay",
        type=nonnegative_float,
        default=10.0,
        help="Seconds to wait before showing the first trivia overlay. Accepts decimals. Default: 10.",
    )
    parser.add_argument(
        "--end-early",
        type=nonnegative_float,
        default=15.0,
        help="Seconds before video end when trivia overlays must finish. Accepts decimals. Default: 15.",
    )
    parser.add_argument(
        "--fade-in-time",
        type=nonnegative_float,
        default=0.5,
        help="Seconds for the first trivia overlay to fade in. Accepts decimals. Use 0 to disable. Default: 0.5.",
    )
    parser.add_argument(
        "--fade-out-time",
        type=nonnegative_float,
        default=0.5,
        help="Seconds for the last trivia overlay to fade out. Accepts decimals. Use 0 to disable. Default: 0.5.",
    )
    parser.add_argument(
        "--mid-question-fade",
        type=nonnegative_float,
        default=0.3,
        help="Seconds to crossfade between questions. Accepts decimals. Use 0 to disable. Default: 0.3.",
    )
    parser.add_argument(
        "--overlay-dir",
        type=Path,
        help="Persist generated overlay PNGs in this directory for inspection.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable live progress updates. Final timing summaries are still shown.",
    )
    return parser.parse_args()


def positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a number") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return parsed


def nonnegative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a number") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be greater than or equal to 0")
    return parsed


def default_output_path(video_file: Path) -> Path:
    return video_file.with_name(f"{video_file.stem}_trivia_countdown.mp4")


def main() -> int:
    total_start = time.monotonic()
    args = parse_args()
    output = args.output or default_output_path(args.video_file)
    progress_reporter = ProgressReporter(enabled=not args.no_progress)

    try:
        validate_input_paths(args.video_file, args.trivia_file)
        require_executable("ffmpeg")
        require_executable("ffprobe")
        dimensions = get_video_dimensions(args.video_file)
        video_duration = get_video_duration(args.video_file)
        video_fps = get_video_fps(args.video_file)
        questions = order_questions(
            load_trivia(args.trivia_file),
            randomize=args.randomize,
            seed=args.seed,
        )
        max_questions = max_full_questions_for_video(
            video_duration,
            args.duration,
            args.answer_duration,
            start_delay=args.start_delay,
            end_early=args.end_early,
        )
        if args.answer_flash_duration > args.answer_duration:
            raise ValueError("--answer-flash-duration cannot exceed --answer-duration")
        if args.mid_question_fade > args.answer_duration:
            raise ValueError("--mid-question-fade cannot exceed --answer-duration")
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if max_questions <= 0:
        print(
            "error: Input video is too short to show even one full trivia question",
            file=sys.stderr,
        )
        return 1

    if args.duration < 1.0:
        print(
            f"warning: Question duration {format_seconds(args.duration)} is less than 1.0s and may be hard to read.",
            file=sys.stderr,
        )
    if args.answer_duration < 1.0:
        print(
            f"warning: Answer highlight duration {format_seconds(args.answer_duration)} is less than 1.0s and may be hard to notice.",
            file=sys.stderr,
        )

    validated_question_count = len(questions)
    questions = questions[:max_questions]

    print(f"Validated {validated_question_count} trivia question(s).")
    print(f"Input video: {args.video_file}")
    print(f"Video dimensions: {dimensions.width}x{dimensions.height}")
    print(f"Video duration: {video_duration:.1f}s")
    print(f"Video FPS: {video_fps:.3f}")
    print(f"Output video: {output}")
    print(f"Question duration: {format_seconds(args.duration)}")
    print(f"Answer highlight duration: approximately {format_seconds(args.answer_duration)}")
    print(f"Answer flash duration: {format_seconds(args.answer_flash_duration)}")
    print(f"Answer flash interval: {format_seconds(args.answer_flash_interval)}")
    print(f"Start delay: {format_seconds(args.start_delay)}")
    print(f"End early: {format_seconds(args.end_early)}")
    print(f"Fade in time: {format_seconds(args.fade_in_time)}")
    print(f"Fade out time: {format_seconds(args.fade_out_time)}")
    print(f"Mid-question fade: {format_seconds(args.mid_question_fade)}")
    if args.randomize:
        seed_note = f" with seed {args.seed}" if args.seed is not None else ""
        print(f"Question order: randomized{seed_note}")
    else:
        print("Question order: CSV order")
    if len(questions) < validated_question_count:
        print(
            f"Using {len(questions)} of {validated_question_count} question(s) based on video length."
        )
    else:
        print(f"Using all {len(questions)} question(s).")
    sys.stdout.flush()

    try:
        overlay_count, persisted_overlay_dir, timings = render_and_compose(
            args.video_file,
            output,
            questions,
            dimensions,
            video_duration=video_duration,
            video_fps=video_fps,
            question_duration=args.duration,
            answer_duration=args.answer_duration,
            answer_flash_duration=args.answer_flash_duration,
            answer_flash_interval=args.answer_flash_interval,
            start_delay=args.start_delay,
            fade_in_time=args.fade_in_time,
            fade_out_time=args.fade_out_time,
            mid_question_fade=args.mid_question_fade,
            overlay_dir=args.overlay_dir,
            progress_reporter=progress_reporter,
        )
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if persisted_overlay_dir:
        print(
            f"Rendered {overlay_count} overlay image(s) in {persisted_overlay_dir} "
            f"in {format_duration(timings.overlay_seconds)}."
        )
    else:
        print(f"Rendered {overlay_count} temporary overlay image(s) in {format_duration(timings.overlay_seconds)}.")
    print(f"Composed video in {format_duration(timings.compose_seconds)}.")
    print(f"Created MP4: {output}")
    print(f"Total time: {format_duration(time.monotonic() - total_start)}.")
    return 0
