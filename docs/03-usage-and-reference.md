# Usage and Command Reference

The desktop instructions apply to the installed Mac app and are the recommended workflow for normal users. Command-line examples are for developers using a source checkout and should be run from the Trivia Countdown project folder.

If you are using the Mac app, start with [Installation](01-installation.md) and [Preparing Trivia Questions](02-preparing-trivia.md). You do not need to install Python, uv, FFmpeg, or use Terminal.

## Create a Video

### Desktop interface

Open **Trivia Countdown** from the Applications folder. If this is the first launch of the ad-hoc-signed preview, complete the [Mac app installation steps](01-installation.md#install-the-mac-app) first.

On the **Main** tab, choose a source video and trivia CSV. The output path initially defaults to `<source-name>_trivia_countdown.mp4` beside the source video, and can be changed with **Output**. The preview is a static frame extracted near the selected question's calculated position, composited with the normal or answer-reveal overlay; it is not video playback.

The **Advanced** tab groups settings into Question Order, Overlay Output, Timing, and Reveal and Transition Effects. It exposes the same defaults as the command line. Settings are reset to their defaults when the app is reopened. **Keep generated overlay PNGs** is off by default. When enabled, use **Browse** to select a directory, type one directly, or let the GUI create `<output-name>_overlays` beside the output MP4. The **Questions** tab is a read-only, scrollable view of all validated rows; its correct answer cells are highlighted, selected rows turn light green, and selecting a row updates the Main preview. Only the first rows that fit the video's capacity are used in the final render. Use the mouse wheel while hovering over the table to scroll it.

When launched from a source checkout, the GUI also has a **CLI** tab with the exact command-line equivalent of the current selections. It includes explicit timing parameters by default. Clear **Include parameters using default values** to omit Advanced values that still match their defaults. The packaged Mac app omits this developer-only tab because DMG users do not have the source command installed. If **Randomize question order** is enabled, use a seed to make the displayed order and final render reproducible; without one, the order may be regenerated differently when rendering.

Select **Create Video** to validate and render. Separate overlay-generation and video-composition progress bars show their current percentage and estimated time remaining. **Cancel Render** stops the active job. The GUI asks before replacing an existing output, and a cancelled or failed render leaves the existing output unchanged. When rendering succeeds, the completed MP4 is at the path shown in **Output MP4**; the app reports completion in the status area.

### Command line

The command line is an advanced workflow for source-checkout users. It is not required when using the packaged Mac app.

Pass the source video and trivia CSV as the two required arguments:

```sh
uv run python make_trivia_countdown.py \
  "/path/to/source-video.mp4" \
  "/path/to/trivia.csv"
```

Keep paths in quotation marks when a file or folder name contains spaces. On macOS, you can drag a file from Finder into Terminal to insert its full path.

The command validates the inputs, reports how many questions fit, renders the trivia panels, and composes the final video. By default, the output is created beside the source video as `<source-name>_trivia_countdown.mp4`.

Video rendering can take several minutes. The duration and resolution of the source video, as well as the Mac's hardware, affect the processing time.

> **Important:** If the output file already exists, it is replaced without a confirmation prompt.

## Common Examples

### Choose the output path

```sh
uv run python make_trivia_countdown.py \
  "/path/to/source-video.mp4" \
  "/path/to/trivia.csv" \
  --output "/path/to/finished-trivia.mp4"
```

### Randomize the questions

Use `--random` to shuffle the questions. Add a seed when you need to reproduce the same order later:

```sh
uv run python make_trivia_countdown.py \
  "/path/to/source-video.mp4" \
  "/path/to/trivia.csv" \
  --random \
  --seed 123
```

## Timing and Video Capacity

The default sequence is:

```text
10-second opening delay
10-second question
2.5-second answer reveal
10-second question
2.5-second answer reveal
...
15-second ending without trivia panels
```

The opening and ending reserves leave time for the underlying countdown video to introduce and conclude the trivia segment. Change them with `--start-delay` and `--end-early`.

Only complete questions that fit within the available time are used. Capacity is calculated as:

```text
available time = video duration - start delay - end-early time
time per question = question duration + answer duration
question capacity = available time rounded down to a whole number of questions
```

For example, a 90-second video with the defaults has 65 seconds available after the 10-second opening delay and 15-second ending reserve. Each question uses 12.5 seconds, so five complete questions fit. If the CSV contains more questions, the extra questions are not rendered. If all questions finish before the reserved ending, the source video continues without trivia panels.

During an answer reveal, the correct answer initially flashes and then remains highlighted. The final portion of the reveal crossfades into the next question. These effects do not add time to the question sequence.

## Command Syntax

```text
uv run python make_trivia_countdown.py VIDEO_FILE TRIVIA_FILE [OPTIONS]
```

### Required arguments

| Argument | Description |
| --- | --- |
| `VIDEO_FILE` | Source video to use behind the trivia panels. |
| `TRIVIA_FILE` | CSV file containing the trivia questions. |

### Output and question order

| Option | Default | Description |
| --- | --- | --- |
| `--output PATH` | `<video-name>_trivia_countdown.mp4` | Set the output MP4 path. Parent folders are created automatically. |
| `--random` | Off | Randomize question order before fitting questions to the video. |
| `--seed INTEGER` | None | Make `--random` produce the same order in later runs. Has no effect without `--random`. |
| `--overlay-dir PATH` | Temporary directory | Keep the generated normal, answer-reveal, and transition PNG files for inspection. |
| `--no-progress` | Off | Hide live progress updates. Final timing summaries are still printed. |

### Timing and transitions

All timing values are measured in seconds and accept decimals.

| Option | Default | Allowed values | Description |
| --- | ---: | --- | --- |
| `--duration` | `10` | Greater than `0` | Time to show each question before revealing the answer. |
| `--answer-duration` | `2.5` | Greater than `0` | Approximate time to show the correct answer. |
| `--answer-flash-duration` | `1.5` | `0` through `--answer-duration` | Initial part of the answer reveal during which the highlight flashes. Set to `0` to disable flashing. |
| `--answer-flash-interval` | `0.2` | `0` or greater | Time between flash state changes. Set to `0` to disable flashing. |
| `--start-delay` | `10` | `0` or greater | Time before the first trivia panel appears. |
| `--end-early` | `15` | `0` or greater | Time reserved at the end of the source video without trivia panels. |
| `--fade-in-time` | `0.5` | `0` or greater | Time for the first trivia panel to fade in. Set to `0` to disable. |
| `--fade-out-time` | `0.5` | `0` or greater | Time for the final trivia panel to fade out. Set to `0` to disable. |
| `--mid-question-fade` | `0.3` | `0` through `--answer-duration` | Time used to crossfade from an answer reveal to the next question. Set to `0` to disable. |

Values under one second are accepted. The tool prints a warning when the main question or answer duration may be too brief to read or notice. Either flash option set to `0` disables answer flashing.

Run the built-in help command at any time for a concise reference:

```sh
uv run python make_trivia_countdown.py --help
```

## Output Behavior

- The source video is read but never modified.
- The output keeps the source video's dimensions and duration.
- Video is encoded as H.264 in an MP4 container.
- Source audio is included when present and encoded as AAC.
- Non-video and non-audio streams, such as embedded subtitles, are not copied.
- Source metadata is copied where FFmpeg supports it.
- The command line overwrites an existing output file at the selected path without confirmation.
- The GUI asks before replacing an existing output. A successful render is encoded to a temporary sibling file and then replaces the output.
- Generated overlay PNGs are temporary and deleted automatically unless `--overlay-dir` is used.

---

[Previous: Preparing Trivia Questions](02-preparing-trivia.md) | [Back to README](../README.md) | [Next: Troubleshooting](04-troubleshooting.md)
