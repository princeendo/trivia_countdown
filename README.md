# Trivia Countdown

Generate an MP4 trivia countdown video by overlaying question and answer panels on top of an existing countdown video.

## Setup

This project uses `uv` for Python dependency management and requires system `ffmpeg` and `ffprobe` to be installed.

```sh
. ./setup_venv.sh
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
  --duration 10 \
  --answer-duration 2.5 \
  --answer-flash-duration 1.5 \
  --answer-flash-interval 0.2 \
  --start-delay 10 \
  --end-early 15 \
  --fade-in-time 0.5 \
  --fade-out-time 0.5 \
  --overlay-dir sample_objects/rendered_overlays \
  --no-progress \
  --random \
  --seed 123
```

`--duration` and `--answer-duration` accept any positive number, including decimals such as `0.75` or `12.5`. `--answer-flash-duration`, `--answer-flash-interval`, `--start-delay`, `--end-early`, `--fade-in-time`, and `--fade-out-time` accept any nonnegative number. Values below `1.0` seconds are allowed, but the script warns when the main question or answer highlight duration may be difficult to notice.

The trivia panel waits `--start-delay` seconds before showing the first question, fades in over `--fade-in-time` seconds, displays each question for `--duration` seconds, then highlights the correct answer for approximately `--answer-duration` seconds. During the first `--answer-flash-duration` seconds of that answer reveal, the correct answer alternates between its normal and highlighted states every `--answer-flash-interval` seconds before ending highlighted and staying solid. The final trivia panel fades out over `--fade-out-time` seconds. Set either flash value to `0` to disable blinking, and set either fade value to `0` to disable that fade. `--answer-flash-duration` cannot exceed `--answer-duration`.

Trivia scheduling also reserves `--end-early` seconds at the end of the source video, so overlays finish before the video ends. If the source video ends before all trivia is shown, the output stops with the video. If trivia ends first, the source video continues without overlays.

Use `--overlay-dir` to persist the generated normal and reveal PNG overlays for visual inspection. Without `--overlay-dir`, generated overlay images are temporary and deleted automatically.

Live progress is shown by default for overlay rendering and video composition, including each phase's percentage, elapsed time, and estimated remaining time. Use `--no-progress` to hide live in-place progress updates. Final timing summaries are still printed, including overlay render time, video composition time, and total time.

The script writes an MP4 using H.264 video and AAC audio. Non-audio/video streams from the input are ignored.
