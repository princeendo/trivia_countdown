"""Command-line interface for trivia countdown video generation."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .app import (
    ProgressEvent,
    RenderOptions,
    RenderRequest,
    default_output_path,
    prepare_render,
    run_render,
)
from .lib.progress import ProgressReporter, format_duration, format_seconds


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


def main() -> int:
    total_start = time.monotonic()
    args = parse_args()
    output = args.output or default_output_path(args.video_file)
    progress_reporter = ProgressReporter(enabled=not args.no_progress)
    options = RenderOptions(
        randomize=args.randomize,
        seed=args.seed,
        question_duration=args.duration,
        answer_duration=args.answer_duration,
        answer_flash_duration=args.answer_flash_duration,
        answer_flash_interval=args.answer_flash_interval,
        start_delay=args.start_delay,
        end_early=args.end_early,
        fade_in_time=args.fade_in_time,
        fade_out_time=args.fade_out_time,
        mid_question_fade=args.mid_question_fade,
        overlay_dir=args.overlay_dir,
    )

    try:
        prepared = prepare_render(RenderRequest(args.video_file, args.trivia_file, output, options))
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for warning in prepared.warnings:
        print(f"warning: {warning}", file=sys.stderr)

    print(f"Validated {prepared.validated_question_count} trivia question(s).")
    print(f"Input video: {args.video_file}")
    print(f"Video dimensions: {prepared.video.dimensions.width}x{prepared.video.dimensions.height}")
    print(f"Video duration: {prepared.video.duration:.1f}s")
    print(f"Video FPS: {prepared.video.fps:.3f}")
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
    if len(prepared.questions) < prepared.validated_question_count:
        print(
            f"Using {len(prepared.questions)} of {prepared.validated_question_count} question(s) based on video length."
        )
    else:
        print(f"Using all {len(prepared.questions)} question(s).")
    sys.stdout.flush()

    phase_starts: dict[str, float] = {}

    def report_progress(event: ProgressEvent) -> None:
        phase_start = phase_starts.setdefault(event.phase, time.monotonic())
        progress_reporter.update_fraction(event.phase, event.fraction, event.detail, phase_start)
        if event.fraction >= 1:
            progress_reporter.complete_phase(event.phase, phase_start)
            phase_starts.pop(event.phase, None)

    try:
        result = run_render(prepared, progress_callback=report_progress)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result.persisted_overlay_dir:
        print(
            f"Rendered {result.overlay_count} overlay image(s) in {result.persisted_overlay_dir} "
            f"in {format_duration(result.timings.overlay_seconds)}."
        )
    else:
        print(
            f"Rendered {result.overlay_count} temporary overlay image(s) "
            f"in {format_duration(result.timings.overlay_seconds)}."
        )
    print(f"Composed video in {format_duration(result.timings.compose_seconds)}.")
    print(f"Created MP4: {output}")
    print(f"Total time: {format_duration(time.monotonic() - total_start)}.")
    return 0
