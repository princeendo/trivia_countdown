"""Trivia CSV parsing and question ordering."""

from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Optional

from .models import REQUIRED_COLUMNS, TriviaQuestion


def load_trivia(path: Path) -> list[TriviaQuestion]:
    with path.open("r", newline="", encoding="utf-8-sig") as trivia_file:
        reader = csv.DictReader(trivia_file)
        fieldnames = reader.fieldnames or []

        if not fieldnames:
            raise ValueError("Trivia CSV is empty")

        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            raise ValueError(f"Trivia CSV is missing required columns: {', '.join(missing_columns)}")

        questions = [
            parse_trivia_row(row_number, row)
            for row_number, row in enumerate(reader, start=2)
            if any((row.get(column) or "").strip() for column in fieldnames)
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
