# Agent Instructions

## Project Overview

This repository contains a Python CLI that generates MP4 trivia countdown videos by rendering question and answer overlays onto an existing countdown video.

The CLI entry point is `make_trivia_countdown.py`. The main implementation lives in the `trivia_countdown/` package. Sample trivia CSV files live in `sample_objects/`. Reference and generated videos are large local artifacts and should not be treated as source files.

## Environment

- Python `>=3.9` is required.
- Dependency management uses `uv`.
- System executables `ffmpeg` and `ffprobe` must be installed and available on `PATH`.
- Runtime Python dependencies are declared in `pyproject.toml` and mirrored in `requirements.txt`.

Set up the environment with:

```sh
. ./setup_venv.sh
```

Run the CLI with:

```sh
uv run python make_trivia_countdown.py input.mp4 trivia.csv
```

A useful sample trivia file is:

```sh
sample_objects/sample_of_5_trivia_questions.csv
```

## Development Guidelines

- Keep changes small and focused; this is currently a compact single-script CLI.
- Preserve existing command-line behavior unless the task explicitly asks for a behavior change.
- Prefer standard-library code unless a dependency is already present or clearly justified.
- Keep user-facing errors and warnings clear, actionable, and written to the appropriate stream.
- Be careful with video-processing paths and temporary files; avoid leaving generated artifacts behind unless the user requested persisted output.
- Do not commit generated videos, rendered overlays, `.venv`, `__pycache__`, `.DS_Store`, or files under `reference_objects/`.

## Trivia CSV Contract

Trivia CSVs must include these columns:

```csv
question,answer_1,answer_2,answer_3,answer_4,correct_answer
```

`correct_answer` must be an integer from `1` to `4`. Additional columns are allowed and ignored.

## Verification

Use lightweight checks first:

```sh
uv run python -m py_compile make_trivia_countdown.py trivia_countdown/*.py trivia_countdown/lib/*.py
uv run python make_trivia_countdown.py --help
```

When changing CSV parsing, argument validation, scheduling, rendering, or composition behavior, run a targeted CLI command with a sample CSV and a known local video if one is available. Full video renders can be slow and require `ffmpeg`/`ffprobe`, so avoid running them unnecessarily.

Before finalizing changes, run:

```sh
git diff --check
```
