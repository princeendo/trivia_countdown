"""Overlay image rendering helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageDraw, ImageFont

from .models import Font, PanelLayout, RenderedOverlay, TransitionFrame, TriviaQuestion, VideoDimensions


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


def render_transition_frames(
    start_path: Path,
    end_path: Path,
    output_directory: Path,
    transition_name: str,
    duration: float,
    fps: float,
) -> tuple[TransitionFrame, ...]:
    if duration <= 0:
        return ()

    frame_count = max(1, round(duration * fps))
    frame_duration = duration / frame_count
    frames: list[TransitionFrame] = []

    with Image.open(start_path) as start_file, Image.open(end_path) as end_file:
        start_image = start_file.convert("RGBA")
        end_image = end_file.convert("RGBA")
        for frame_index in range(1, frame_count + 1):
            alpha = frame_index / frame_count
            frame_path = output_directory / f"{transition_name}_{frame_index:04d}.png"
            Image.blend(start_image, end_image, alpha).save(frame_path)
            frames.append(TransitionFrame(frame_path, frame_duration))

    return tuple(frames)


def render_overlays(
    questions: list[TriviaQuestion],
    dimensions: VideoDimensions,
    output_directory: Path,
    mid_question_fade: float,
    video_fps: float,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[RenderedOverlay]:
    output_directory.mkdir(parents=True, exist_ok=True)
    rendered_paths: list[RenderedOverlay] = []
    transition_frame_count = max(1, round(mid_question_fade * video_fps)) if mid_question_fade > 0 else 0
    total_images = len(questions) * 2 + max(0, len(questions) - 1) * transition_frame_count
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

        rendered_paths.append(RenderedOverlay(normal_path, reveal_path))

    if mid_question_fade > 0:
        overlays_with_transitions: list[RenderedOverlay] = []
        for index, overlay in enumerate(rendered_paths):
            transition_frames: tuple[TransitionFrame, ...] = ()
            if index < len(rendered_paths) - 1:
                transition_frames = render_transition_frames(
                    overlay.reveal_path,
                    rendered_paths[index + 1].normal_path,
                    output_directory,
                    f"question_{index + 1:04d}_to_{index + 2:04d}_transition",
                    mid_question_fade,
                    video_fps,
                )
                completed_images += len(transition_frames)
                if progress_callback:
                    progress_callback(completed_images, total_images)
            overlays_with_transitions.append(
                RenderedOverlay(overlay.normal_path, overlay.reveal_path, transition_frames)
            )
        rendered_paths = overlays_with_transitions

    return rendered_paths
