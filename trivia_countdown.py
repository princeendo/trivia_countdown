#!/usr/bin/env python3
"""Generate trivia countdown videos from a source video and CSV questions."""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import threading
import time
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Optional, Union

from PIL import Image, ImageDraw, ImageFont


Font = Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]


REQUIRED_COLUMNS = [
    "question",
    "answer_1",
    "answer_2",
    "answer_3",
    "answer_4",
    "correct_answer",
]


@dataclass(frozen=True)
class TriviaQuestion:
    question: str
    answers: tuple[str, str, str, str]
    correct_answer: int


@dataclass(frozen=True)
class VideoDimensions:
    width: int
    height: int


@dataclass(frozen=True)
class PanelLayout:
    question_box: tuple[int, int, int, int]
    answer_boxes: tuple[tuple[int, int, int, int], ...]
    corner_radius: int
    outline_width: int
    question_font_size: int
    answer_font_size: int


@dataclass(frozen=True)
class RenderTimings:
    overlay_seconds: float
    compose_seconds: float


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
        default=15.0,
        help="Seconds to show each question before revealing the answer. Accepts decimals. Default: 15.",
    )
    parser.add_argument(
        "--answer-duration",
        type=positive_float,
        default=3.0,
        help="Approximate seconds to highlight the correct answer. Accepts decimals. Default: 3.",
    )
    parser.add_argument(
        "--answer-flash-duration",
        type=nonnegative_float,
        default=1.0,
        help=(
            "Seconds for the answer to alternate between normal and highlighted before staying solid. "
            "Accepts decimals. Use 0 to disable blinking. Default: 1."
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
        default=5.0,
        help="Seconds to wait before showing the first trivia overlay. Accepts decimals. Default: 5.",
    )
    parser.add_argument(
        "--end-early",
        type=nonnegative_float,
        default=5.0,
        help="Seconds before video end when trivia overlays must finish. Accepts decimals. Default: 5.",
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


def format_seconds(value: float) -> str:
    return f"{value:g}s"


def format_duration(seconds: float) -> str:
    seconds = max(0.0, seconds)
    if seconds < 60:
        return f"{seconds:.1f}s"

    total_seconds = round(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, remaining_seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {remaining_seconds:02d}s"
    return f"{minutes}m {remaining_seconds:02d}s"


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


class ProgressReporter:
    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled

    def update_units(self, phase: str, completed: int, total: int, phase_start: float) -> None:
        if total <= 0:
            return
        fraction = min(1.0, max(0.0, completed / total))
        detail = f"{completed}/{total}"
        self.update_fraction(phase, fraction, detail, phase_start)

    def update_fraction(self, phase: str, fraction: float, detail: str, phase_start: float) -> None:
        if not self.enabled:
            return

        fraction = min(1.0, max(0.0, fraction))
        elapsed = time.monotonic() - phase_start
        if fraction > 0:
            remaining = elapsed * (1 - fraction) / fraction
            remaining_text = format_duration(remaining)
        else:
            remaining_text = "calculating"

        message = (
            f"{phase}: {fraction * 100:5.1f}% ({detail}) "
            f"elapsed {format_duration(elapsed)}, remaining {remaining_text}"
        )
        print(f"\r{message}\033[K", end="", file=sys.stderr, flush=True)

    def complete_phase(self, phase: str, phase_start: float) -> None:
        if not self.enabled:
            return
        elapsed = time.monotonic() - phase_start
        print(f"\r{phase}: complete in {format_duration(elapsed)}\033[K", file=sys.stderr, flush=True)


def default_output_path(video_file: Path) -> Path:
    return video_file.with_name(f"{video_file.stem}_trivia_countdown.mp4")


def require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required executable not found: {name}")


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


def validate_input_paths(video_file: Path, trivia_file: Path) -> None:
    if not video_file.is_file():
        raise ValueError(f"Video file does not exist: {video_file}")
    if not trivia_file.is_file():
        raise ValueError(f"Trivia CSV does not exist: {trivia_file}")


def load_trivia(path: Path) -> list[TriviaQuestion]:
    try:
        dataframe = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("Trivia CSV is empty") from exc

    fieldnames = list(dataframe.columns)
    if not fieldnames:
        raise ValueError("Trivia CSV is empty")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing_columns:
        raise ValueError(f"Trivia CSV is missing required columns: {', '.join(missing_columns)}")

    trimmed_dataframe = dataframe[REQUIRED_COLUMNS].fillna("")
    questions = [
        parse_trivia_row(row_number, row)
        for row_number, row in enumerate(trimmed_dataframe.to_dict("records"), start=2)
    ]

    if not questions:
        raise ValueError("Trivia CSV does not contain any questions")
    return questions


def parse_trivia_row(row_number: int, row: dict[str, str]) -> TriviaQuestion:
    text_values = {column: (row.get(column) or "").strip() for column in REQUIRED_COLUMNS}
    empty_columns = [column for column, value in text_values.items() if not value]
    if empty_columns:
        raise ValueError(f"Row {row_number} has empty required columns: {', '.join(empty_columns)}")

    try:
        correct_answer = int(text_values["correct_answer"])
    except ValueError as exc:
        raise ValueError(f"Row {row_number} correct_answer must be an integer from 1 to 4") from exc

    if correct_answer not in {1, 2, 3, 4}:
        raise ValueError(f"Row {row_number} correct_answer must be an integer from 1 to 4")

    return TriviaQuestion(
        question=text_values["question"],
        answers=(
            text_values["answer_1"],
            text_values["answer_2"],
            text_values["answer_3"],
            text_values["answer_4"],
        ),
        correct_answer=correct_answer,
    )


def order_questions(
    questions: list[TriviaQuestion],
    *,
    randomize: bool,
    seed: Optional[int],
) -> list[TriviaQuestion]:
    ordered = list(questions)
    if randomize:
        rng = random.Random(seed)
        rng.shuffle(ordered)
    return ordered


def max_full_questions_for_video(
    video_duration: float,
    question_duration: float,
    answer_duration: float,
    *,
    start_delay: float,
    end_early: float,
) -> int:
    available_duration = video_duration - start_delay - end_early
    if available_duration <= 0:
        return 0
    segment_duration = question_duration + answer_duration
    return int(available_duration // segment_duration)


def scale_rect(rect: tuple[int, int, int, int], dimensions: VideoDimensions) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = rect
    return (
        round(x1 * dimensions.width / 1920),
        round(y1 * dimensions.height / 1080),
        round(x2 * dimensions.width / 1920),
        round(y2 * dimensions.height / 1080),
    )


def expand_rect(
    rect: tuple[int, int, int, int],
    *,
    width_factor: float,
    height_factor: float,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = rect
    width = x2 - x1
    height = y2 - y1
    extra_width = width * (width_factor - 1) / 2
    extra_height = height * (height_factor - 1) / 2
    return (
        round(x1 - extra_width),
        round(y1 - extra_height),
        round(x2 + extra_width),
        round(y2 + extra_height),
    )


def build_panel_layout(dimensions: VideoDimensions) -> PanelLayout:
    scale = min(dimensions.width / 1920, dimensions.height / 1080)
    return PanelLayout(
        question_box=scale_rect(expand_rect((185, 690, 1735, 792), width_factor=1.15, height_factor=1.15), dimensions),
        answer_boxes=(
            scale_rect(expand_rect((150, 820, 930, 890), width_factor=1.05, height_factor=1.15), dimensions),
            scale_rect(expand_rect((990, 820, 1770, 890), width_factor=1.05, height_factor=1.15), dimensions),
            scale_rect(expand_rect((150, 920, 930, 990), width_factor=1.05, height_factor=1.15), dimensions),
            scale_rect(expand_rect((990, 920, 1770, 990), width_factor=1.05, height_factor=1.15), dimensions),
        ),
        corner_radius=max(10, round(24 * scale)),
        outline_width=max(2, round(4 * scale)),
        question_font_size=max(16, round(55 * scale)),
        answer_font_size=max(14, round(40 * scale)),
    )


def load_font(size: int, *, bold: bool = False) -> Font:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: Font) -> tuple[int, int]:
    left, top, right, bottom = draw.multiline_textbbox((0, 0), text, font=font, spacing=8)
    return right - left, bottom - top


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: Font) -> tuple[int, int, int, int]:
    return draw.multiline_textbbox((0, 0), text, font=font, spacing=8)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: Font, max_width: int) -> str:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if text_size(draw, candidate, font)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return "\n".join(lines)


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    starting_size: int,
    *,
    bold: bool = False,
) -> tuple[str, Font]:
    x1, y1, x2, y2 = box
    max_width = max(1, x2 - x1)
    max_height = max(1, y2 - y1)
    minimum_size = 14
    for size in range(starting_size, minimum_size - 1, -2):
        font = load_font(size, bold=bold)
        wrapped = wrap_text(draw, text, font, max_width)
        width, height = text_size(draw, wrapped, font)
        if width <= max_width and height <= max_height:
            return wrapped, font

    font = load_font(minimum_size, bold=bold)
    return wrap_text(draw, text, font, max_width), font


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    starting_size: int,
    fill: tuple[int, int, int, int],
    *,
    bold: bool = False,
) -> None:
    x1, y1, x2, y2 = box
    horizontal_padding = max(10, round((x2 - x1) * 0.045))
    vertical_padding = max(8, round((y2 - y1) * 0.16))
    text_box = (
        x1 + horizontal_padding,
        y1 + vertical_padding,
        x2 - horizontal_padding,
        y2 - vertical_padding,
    )
    wrapped, font = fit_text(draw, text, text_box, starting_size, bold=bold)
    left, top, right, bottom = text_bbox(draw, wrapped, font)
    width = right - left
    height = bottom - top
    text_x = text_box[0] + ((text_box[2] - text_box[0] - width) / 2) - left
    text_y = text_box[1] + ((text_box[3] - text_box[1] - height) / 2) - top
    draw.multiline_text((text_x, text_y), wrapped, font=font, fill=fill, anchor=None, align="center", spacing=8)


def draw_panel_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    layout: PanelLayout,
    *,
    highlighted: bool = False,
) -> None:
    fill = (255, 224, 36, 230) if highlighted else (11, 34, 82, 220)
    outline = (255, 239, 124, 255) if highlighted else (60, 177, 255, 255)
    draw.rounded_rectangle(
        box,
        radius=layout.corner_radius,
        fill=fill,
        outline=outline,
        width=layout.outline_width,
    )


def draw_clean_panel(draw: ImageDraw.ImageDraw, layout: PanelLayout) -> None:
    draw_panel_box(draw, layout.question_box, layout)
    for answer_box in layout.answer_boxes:
        draw_panel_box(draw, answer_box, layout)


def render_question_overlay(
    question: TriviaQuestion,
    dimensions: VideoDimensions,
    output_path: Path,
    *,
    reveal_answer: bool,
) -> None:
    layout = build_panel_layout(dimensions)
    image = Image.new("RGBA", (dimensions.width, dimensions.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw_clean_panel(draw, layout)
    draw_centered_text(
        draw,
        question.question,
        layout.question_box,
        layout.question_font_size,
        (255, 255, 255, 255),
        bold=True,
    )

    for index, answer_box in enumerate(layout.answer_boxes, start=1):
        highlighted = reveal_answer and index == question.correct_answer
        if highlighted:
            draw_panel_box(draw, answer_box, layout, highlighted=True)
        text_fill = (24, 24, 24, 255) if highlighted else (255, 255, 255, 255)
        draw_centered_text(
            draw,
            question.answers[index - 1],
            answer_box,
            layout.answer_font_size,
            text_fill,
            bold=True,
        )

    image.save(output_path)


def render_overlays(
    questions: list[TriviaQuestion],
    dimensions: VideoDimensions,
    output_directory: Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[tuple[Path, Path]]:
    output_directory.mkdir(parents=True, exist_ok=True)
    rendered_paths: list[tuple[Path, Path]] = []
    total_images = len(questions) * 2
    completed_images = 0
    for index, question in enumerate(questions, start=1):
        normal_path = output_directory / f"question_{index:04d}_normal.png"
        reveal_path = output_directory / f"question_{index:04d}_reveal.png"
        render_question_overlay(question, dimensions, normal_path, reveal_answer=False)
        completed_images += 1
        if progress_callback:
            progress_callback(completed_images, total_images)
        render_question_overlay(question, dimensions, reveal_path, reveal_answer=True)
        completed_images += 1
        if progress_callback:
            progress_callback(completed_images, total_images)
        rendered_paths.append((normal_path, reveal_path))
    return rendered_paths


def quote_ffconcat_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace("'", "\\'")


def build_overlay_schedule(
    overlay_paths: list[tuple[Path, Path]],
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

    for normal_path, reveal_path in overlay_paths:
        add_overlay_window(normal_path, question_duration)

        flash_end = min(answer_flash_duration, answer_duration)
        flash_enabled = answer_flash_duration > 0 and answer_flash_interval > 0
        if flash_enabled and flash_end > 0:
            flash_window_duration = flash_end
            flash_chunk_count = max(1, int(flash_window_duration // answer_flash_interval))
            flash_chunk_duration = flash_window_duration / flash_chunk_count
            flash_start_time = 0.0
            chunk_index = 0

            while flash_start_time < flash_end:
                chunk_end_time = min(flash_start_time + flash_chunk_duration, flash_end)
                use_reveal_overlay = chunk_index % 2 == 1 or chunk_end_time >= answer_duration
                add_overlay_window(
                    reveal_path if use_reveal_overlay else normal_path,
                    chunk_end_time - flash_start_time,
                )
                flash_start_time = chunk_end_time
                chunk_index += 1
        else:
            flash_end = 0.0

        add_overlay_window(reveal_path, answer_duration - flash_end)

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


def build_filter_graph() -> str:
    filters = [
        "[0:v]format=rgba[base]",
        "[1:v]format=rgba[overlay]",
        "[base][overlay]overlay=0:0:format=auto:eof_action=pass,format=yuv420p[vout]",
    ]

    return ";".join(filters)


def compose_video(
    video_file: Path,
    output_file: Path,
    overlay_paths: list[tuple[Path, Path]],
    dimensions: VideoDimensions,
    *,
    video_duration: float,
    question_duration: float,
    answer_duration: float,
    answer_flash_duration: float,
    answer_flash_interval: float,
    start_delay: float,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

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
                build_filter_graph(),
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


def render_and_compose(
    video_file: Path,
    output_file: Path,
    questions: list[TriviaQuestion],
    dimensions: VideoDimensions,
    *,
    video_duration: float,
    question_duration: float,
    answer_duration: float,
    answer_flash_duration: float,
    answer_flash_interval: float,
    start_delay: float,
    overlay_dir: Optional[Path],
    progress_reporter: ProgressReporter,
) -> tuple[int, Optional[Path], RenderTimings]:
    overlay_start = time.monotonic()

    def report_overlay_progress(completed: int, total: int) -> None:
        progress_reporter.update_units("Rendering overlays", completed, total, overlay_start)

    if overlay_dir:
        overlay_paths = render_overlays(questions, dimensions, overlay_dir, report_overlay_progress)
        progress_reporter.complete_phase("Rendering overlays", overlay_start)
        overlay_seconds = time.monotonic() - overlay_start

        compose_start = time.monotonic()

        def report_compose_progress(encoded_seconds: float) -> None:
            fraction = encoded_seconds / video_duration if video_duration > 0 else 0.0
            detail = f"{format_duration(encoded_seconds)}/{format_duration(video_duration)}"
            progress_reporter.update_fraction("Composing video", fraction, detail, compose_start)

        compose_video(
            video_file,
            output_file,
            overlay_paths,
            dimensions,
            video_duration=video_duration,
            question_duration=question_duration,
            answer_duration=answer_duration,
            answer_flash_duration=answer_flash_duration,
            answer_flash_interval=answer_flash_interval,
            start_delay=start_delay,
            progress_callback=report_compose_progress,
        )
        progress_reporter.complete_phase("Composing video", compose_start)
        compose_seconds = time.monotonic() - compose_start
        return len(overlay_paths) * 2, overlay_dir, RenderTimings(overlay_seconds, compose_seconds)

    with TemporaryDirectory(prefix="trivia_countdown_") as temporary_directory:
        overlay_paths = render_overlays(questions, dimensions, Path(temporary_directory), report_overlay_progress)
        progress_reporter.complete_phase("Rendering overlays", overlay_start)
        overlay_seconds = time.monotonic() - overlay_start

        compose_start = time.monotonic()

        def report_compose_progress(encoded_seconds: float) -> None:
            fraction = encoded_seconds / video_duration if video_duration > 0 else 0.0
            detail = f"{format_duration(encoded_seconds)}/{format_duration(video_duration)}"
            progress_reporter.update_fraction("Composing video", fraction, detail, compose_start)

        compose_video(
            video_file,
            output_file,
            overlay_paths,
            dimensions,
            video_duration=video_duration,
            question_duration=question_duration,
            answer_duration=answer_duration,
            answer_flash_duration=answer_flash_duration,
            answer_flash_interval=answer_flash_interval,
            start_delay=start_delay,
            progress_callback=report_compose_progress,
        )
        progress_reporter.complete_phase("Composing video", compose_start)
        compose_seconds = time.monotonic() - compose_start
        return len(overlay_paths) * 2, None, RenderTimings(overlay_seconds, compose_seconds)


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
    print(f"Output video: {output}")
    print(f"Question duration: {format_seconds(args.duration)}")
    print(f"Answer highlight duration: approximately {format_seconds(args.answer_duration)}")
    print(f"Answer flash duration: {format_seconds(args.answer_flash_duration)}")
    print(f"Answer flash interval: {format_seconds(args.answer_flash_interval)}")
    print(f"Start delay: {format_seconds(args.start_delay)}")
    print(f"End early: {format_seconds(args.end_early)}")
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
            question_duration=args.duration,
            answer_duration=args.answer_duration,
            answer_flash_duration=args.answer_flash_duration,
            answer_flash_interval=args.answer_flash_interval,
            start_delay=args.start_delay,
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


if __name__ == "__main__":
    raise SystemExit(main())
