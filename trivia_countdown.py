#!/usr/bin/env python3
"""Generate trivia countdown videos from a source video and CSV questions."""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Union

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
        "--overlay-dir",
        type=Path,
        help="Persist generated overlay PNGs in this directory for inspection.",
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


def format_seconds(value: float) -> str:
    return f"{value:g}s"


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


def max_full_questions_for_video(video_duration: float, question_duration: float, answer_duration: float) -> int:
    segment_duration = question_duration + answer_duration
    return int(video_duration // segment_duration)


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
) -> list[tuple[Path, Path]]:
    output_directory.mkdir(parents=True, exist_ok=True)
    rendered_paths: list[tuple[Path, Path]] = []
    for index, question in enumerate(questions, start=1):
        normal_path = output_directory / f"question_{index:04d}_normal.png"
        reveal_path = output_directory / f"question_{index:04d}_reveal.png"
        render_question_overlay(question, dimensions, normal_path, reveal_answer=False)
        render_question_overlay(question, dimensions, reveal_path, reveal_answer=True)
        rendered_paths.append((normal_path, reveal_path))
    return rendered_paths


def build_filter_graph(
    overlay_paths: list[tuple[Path, Path]],
    *,
    question_duration: float,
    answer_duration: float,
) -> str:
    filters = ["[0:v]format=rgba[v0]"]
    current_label = "v0"
    overlay_input_index = 1
    output_index = 1

    for question_index, _paths in enumerate(overlay_paths):
        question_start = question_index * (question_duration + answer_duration)
        reveal_start = question_start + question_duration
        windows = (
            (question_start, reveal_start),
            (reveal_start, reveal_start + answer_duration),
        )

        for start_time, end_time in windows:
            overlay_label = f"ov{overlay_input_index}"
            next_label = f"v{output_index}"
            filters.append(f"[{overlay_input_index}:v]format=rgba[{overlay_label}]")
            filters.append(
                f"[{current_label}][{overlay_label}]"
                f"overlay=0:0:enable='between(t,{start_time:.3f},{end_time:.3f})'"
                f"[{next_label}]"
            )
            current_label = next_label
            overlay_input_index += 1
            output_index += 1

    filters.append(f"[{current_label}]format=yuv420p[vout]")
    return ";".join(filters)


def compose_video(
    video_file: Path,
    output_file: Path,
    overlay_paths: list[tuple[Path, Path]],
    *,
    video_duration: float,
    question_duration: float,
    answer_duration: float,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    command = ["ffmpeg", "-y", "-i", str(video_file)]
    for normal_path, reveal_path in overlay_paths:
        command.extend(["-loop", "1", "-i", str(normal_path)])
        command.extend(["-loop", "1", "-i", str(reveal_path)])

    command.extend(
        [
            "-filter_complex",
            build_filter_graph(
                overlay_paths,
                question_duration=question_duration,
                answer_duration=answer_duration,
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
            "-movflags",
            "+faststart",
            str(output_file),
        ]
    )

    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or "ffmpeg failed while composing the output video"
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
    overlay_dir: Optional[Path],
) -> tuple[int, Optional[Path]]:
    if overlay_dir:
        overlay_paths = render_overlays(questions, dimensions, overlay_dir)
        compose_video(
            video_file,
            output_file,
            overlay_paths,
            video_duration=video_duration,
            question_duration=question_duration,
            answer_duration=answer_duration,
        )
        return len(overlay_paths) * 2, overlay_dir

    with TemporaryDirectory(prefix="trivia_countdown_") as temporary_directory:
        overlay_paths = render_overlays(questions, dimensions, Path(temporary_directory))
        compose_video(
            video_file,
            output_file,
            overlay_paths,
            video_duration=video_duration,
            question_duration=question_duration,
            answer_duration=answer_duration,
        )
        return len(overlay_paths) * 2, None


def main() -> int:
    args = parse_args()
    output = args.output or default_output_path(args.video_file)

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
        )
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

    try:
        overlay_count, persisted_overlay_dir = render_and_compose(
            args.video_file,
            output,
            questions,
            dimensions,
            video_duration=video_duration,
            question_duration=args.duration,
            answer_duration=args.answer_duration,
            overlay_dir=args.overlay_dir,
        )
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if persisted_overlay_dir:
        print(f"Rendered {overlay_count} overlay image(s) in {persisted_overlay_dir}.")
    else:
        print(f"Rendered {overlay_count} temporary overlay image(s).")
    print(f"Created MP4: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
