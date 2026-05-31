"""Shared data models for trivia countdown rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from PIL import ImageFont


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


@dataclass(frozen=True)
class TransitionFrame:
    path: Path
    duration: float


@dataclass(frozen=True)
class RenderedOverlay:
    normal_path: Path
    reveal_path: Path
    transition_frames: tuple[TransitionFrame, ...] = ()
