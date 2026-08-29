# Agent Instructions

## Project Overview

This repository contains a Python CLI that generates MP4 trivia countdown videos by rendering question and answer overlays onto an existing countdown video.

The CLI entry point is `make_trivia_countdown.py`. The main implementation lives in the `trivia_countdown/` package. Sample trivia CSV files live in `sample_objects/`. Reference and generated videos are large local artifacts and should not be treated as source files.

## Environment

- Python `>=3.9` is required.
- Dependency management uses `uv`.
- Source-mode executables `ffmpeg` and `ffprobe` must be installed and available on `PATH`.
- Runtime Python dependencies are declared in `pyproject.toml` and mirrored in `requirements.txt`.

On macOS or Linux, set up the environment with:

```sh
. ./setup_venv.sh
```

On Windows PowerShell, run commands directly without activating an environment:

```powershell
uv sync --frozen
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
- Before finalizing any change, compare the implementation and current diff with `README.md` and every file under `docs/`. Update the documentation in the same change whenever behavior, commands, defaults, dependencies, setup steps, file paths, platform support, or user workflows have changed, and verify that links and duplicated guidance remain consistent.

## Trivia CSV Contract

Trivia CSVs must include these columns:

```csv
question,answer_1,answer_2,answer_3,answer_4,correct_answer
```

`correct_answer` must be an integer from `1` to `4`. Additional columns are allowed and ignored.

## Verification

Use lightweight checks first:

```sh
uv run python -m compileall -q make_trivia_countdown.py make_trivia_countdown_gui.py trivia_countdown
uv run python make_trivia_countdown.py --help
```

When changing CSV parsing, argument validation, scheduling, rendering, or composition behavior, run a targeted CLI command with a sample CSV and a known local video if one is available. Full video renders can be slow and require `ffmpeg`/`ffprobe`, so avoid running them unnecessarily.

For a Windows package build, use a Windows x64 system with Inno Setup 7.1.0 and run:

```powershell
.\scripts\build_windows_installer.ps1
```

Do not publish the resulting installer until the required FFmpeg corresponding-source archive and clean-machine qualification are complete.

Before finalizing changes, run:

```sh
git diff --check
```
