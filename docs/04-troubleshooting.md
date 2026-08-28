# Troubleshooting

## `brew: command not found`

Install Homebrew by following the instructions at [brew.sh](https://brew.sh/), then open a new Terminal window and run `brew install uv ffmpeg` again.

## `uv: command not found`

Run `brew install uv`. If Homebrew reports that `uv` is already installed, open a new Terminal window so its updated command path is loaded.

## `Required executable not found: ffmpeg` or `ffprobe`

Run `brew install ffmpeg`. The Homebrew FFmpeg package supplies both commands.

## The Desktop Interface Does Not Open

Launch it from the project folder with `uv run python make_trivia_countdown_gui.py`. If it reports that Tkinter is unavailable, use a Python installation that includes Tcl/Tk support, then run `. ./setup_venv.sh` again. The project is currently verified on macOS.

## The Preview Is Unavailable or Looks Different From the Video

The GUI preview is a single frame extracted by FFmpeg, not embedded video playback. Confirm that FFmpeg can read the source video and select a different question if its scheduled timestamp is close to the end of the video. The source file is never modified.

## I Cancelled a Render

The GUI stops rendering as soon as the active image or FFmpeg operation reaches a cancellation check. A partially encoded temporary file is removed, and an existing selected output remains unchanged. It can take a short time for FFmpeg to stop after selecting **Cancel Render**.

## `Video file does not exist` or `Trivia CSV does not exist`

Confirm the path and keep it in quotation marks if any folder or filename contains spaces. Dragging the file from Finder into Terminal is a reliable way to insert its full path.

## `Input video is too short to show even one full trivia question`

The video does not have enough time for one question after the opening and ending reserves. Use a longer video or reduce values such as `--start-delay`, `--end-early`, `--duration`, or `--answer-duration`.

For example, remove the opening and ending reserves with:

```sh
uv run python make_trivia_countdown.py \
  "/path/to/source-video.mp4" \
  "/path/to/trivia.csv" \
  --start-delay 0 \
  --end-early 0
```

See [Timing and Video Capacity](03-usage-and-reference.md#timing-and-video-capacity) for an explanation of how many questions fit.

## The CSV Reports Missing Columns or an Invalid Row

Compare the header with the required column names and inspect the row number shown in the error. Every required field must be nonempty, and `correct_answer` must contain an integer from `1` to `4`.

See [Preparing Trivia Questions](02-preparing-trivia.md) for the complete CSV contract and an example.

## Text Is Too Small or Difficult to Read

Question and answer text wraps and shrinks automatically, but unusually long text may still be difficult to read. Shorten the wording, render a brief test, or use `--overlay-dir preview_overlays` to inspect the generated PNG files.

## Rendering Takes a Long Time

The complete source video is re-encoded. Long or high-resolution videos can take several minutes or more, particularly on older hardware. Closing other processor-intensive applications may help.

## Requesting Help

If a problem is not covered above, see [Support Information](05-limitations-privacy-and-support.md#support-information) for what to include when requesting help.

---

[Previous: Usage and Command Reference](03-usage-and-reference.md) | [Back to README](../README.md) | [Next: Limitations, Privacy, and Support](05-limitations-privacy-and-support.md)
