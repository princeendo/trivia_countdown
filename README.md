# Trivia Countdown

Generate an MP4 trivia countdown video by overlaying question and answer panels on top of an existing countdown video.

## Setup

This project uses `uv` for Python dependency management and requires system `ffmpeg` and `ffprobe` to be installed.

```sh
uv sync
```

## Trivia CSV Format

The trivia file must be a CSV that includes these columns:

```csv
question,answer_1,answer_2,answer_3,answer_4,correct_answer
```

`correct_answer` must be an integer from `1` to `4`, corresponding to `answer_1` through `answer_4`.

Additional columns are allowed and ignored. For example, a `difficulty` column will not affect parsing.

## Usage

```sh
uv run python trivia_countdown.py input.mp4 trivia.csv
```

By default, the output path is derived from the input video name:

```text
input_trivia_countdown.mp4
```

Optional arguments:

```sh
uv run python trivia_countdown.py input.mp4 trivia.csv \
  --output output.mp4 \
  --duration 15.5 \
  --answer-duration 3.25 \
  --start-delay 1.0 \
  --end-early 1.0 \
  --overlay-dir sample_objects/rendered_overlays \
  --random \
  --seed 123
```

`--duration`, `--answer-duration`, `--start-delay`, and `--end-early` accept any positive number, including decimals such as `0.75` or `12.5`. Values below `1.0` seconds are allowed, but the script warns because the question or answer highlight may be difficult to see.

The trivia panel waits `--start-delay` seconds before showing the first question, displays each question for `--duration` seconds, then highlights the correct answer for approximately `--answer-duration` seconds. Trivia scheduling also reserves `--end-early` seconds at the end of the source video, so overlays finish before the video ends. If the source video ends before all trivia is shown, the output stops with the video. If trivia ends first, the source video continues without overlays.

Use `--overlay-dir` to persist the generated normal and reveal PNG overlays for visual inspection. Without `--overlay-dir`, generated overlay images are temporary and deleted automatically.

The script writes an MP4 using H.264 video and AAC audio. Non-audio/video streams from the input are ignored.
