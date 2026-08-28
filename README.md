# Trivia Countdown

Create an MP4 trivia countdown by placing question and answer panels over an existing video. Each question appears for a configurable amount of time, then the correct answer is highlighted before the next question begins.

![Animated example showing a trivia question, answer reveal, and transition to the next question](assets/trivia-demo.gif)

Trivia Countdown runs locally on your Mac. It does not upload your video or trivia questions, and it does not modify the source video.

## What You Need

- A Mac and access to the Terminal application
- A countdown or background video supported by FFmpeg, such as an MP4
- A CSV file containing your trivia questions
- Enough free disk space for a newly encoded copy of the video

This repository includes a sample trivia CSV, but it does not include a source video. You must provide the video that will appear behind the trivia panels.

Trivia Countdown is currently supported on macOS. Other operating systems may work, but their setup and font rendering have not been verified.

## Download and Install

### 1. Download the project

On the [Trivia Countdown GitHub page](https://github.com/princeendo/trivia_countdown), select **Code**, then **Download ZIP**. Open the downloaded ZIP file to extract the project folder.

### 2. Open the project in Terminal

Open **Terminal** from **Applications > Utilities**. Type `cd `, including the space, drag the extracted project folder into the Terminal window, and press Return.

Your command will look similar to this:

```sh
cd /Users/your-name/Downloads/trivia_countdown-main
```

### 3. Install the required tools

The project uses [Homebrew](https://brew.sh/) to install `uv` and FFmpeg. If Homebrew is not already installed, follow the installation instructions on its official website first.

From the project folder in Terminal, run:

```sh
brew install uv ffmpeg
```

`uv` manages the Python environment and installs the Python package required by this project. FFmpeg and its companion tool, `ffprobe`, inspect and process the video.

### 4. Set up the Python environment

Run:

```sh
. ./setup_venv.sh
```

The script creates a local `.venv` environment, installs the project dependencies, and activates the environment in the current Terminal session. To confirm that the command-line tool is available, run:

```sh
uv run python make_trivia_countdown.py --help
```

You should see the available arguments and options. You only need to repeat the setup command after downloading a new copy of the project or when its dependencies change.

## Create Your First Video

The repository includes a five-question sample at `sample_objects/sample_of_5_trivia_questions.csv`. Use it for your first render so you can verify the installation before preparing your own questions.

Run the following command, replacing the example video path with the location of your source video:

```sh
uv run python make_trivia_countdown.py \
  "/Users/your-name/Movies/countdown.mp4" \
  sample_objects/sample_of_5_trivia_questions.csv
```

Keep paths in quotation marks when a file or folder name contains spaces. On macOS, you can drag a file from Finder into Terminal to insert its full path.

The command validates the inputs, reports how many questions fit, renders the trivia panels, and composes the final video. With the example above, the output is created beside the source video as:

```text
/Users/your-name/Movies/countdown_trivia_countdown.mp4
```

Video rendering can take several minutes. The duration and resolution of the source video, as well as the Mac's hardware, affect the processing time.

> **Important:** If the output file already exists, it is replaced without a confirmation prompt. Choose a different path with `--output` if you need to preserve an earlier render.

## Prepare a Trivia CSV

The first row of the CSV must contain these column names exactly:

```csv
question,answer_1,answer_2,answer_3,answer_4,correct_answer
What planet is known as the Red Planet?,Venus,Mars,Jupiter,Saturn,2
Which element has the chemical symbol O?,Gold,Oxygen,Silver,Iron,2
```

| Column | Description |
| --- | --- |
| `question` | The question shown above the four answers. |
| `answer_1` | The first answer choice. |
| `answer_2` | The second answer choice. |
| `answer_3` | The third answer choice. |
| `answer_4` | The fourth answer choice. |
| `correct_answer` | The number `1`, `2`, `3`, or `4` identifying the correct answer choice. |

`correct_answer` contains the answer number, not the answer text. In the first example row, `2` means that `answer_2` (`Mars`) is highlighted.

Every required value must be present. Empty rows are ignored, and additional columns are allowed and ignored. Files may use UTF-8 with or without a byte order mark.

### Using a spreadsheet

You can prepare questions in Numbers, Excel, Google Sheets, or another spreadsheet application:

1. Put the required column names in the first row.
2. Enter one question per row.
3. Export or download the sheet as a UTF-8 CSV file.
4. Open the exported file once to confirm that the header and questions are present.

Spreadsheet applications handle commas and quotation marks in cells when exporting. If you edit the CSV by hand, follow standard CSV quoting rules for values that contain commas, quotation marks, or line breaks.

The complete sample file is available at [`sample_objects/sample_of_5_trivia_questions.csv`](sample_objects/sample_of_5_trivia_questions.csv).

## Use Your Own Questions

Pass your source video and trivia CSV as the two required arguments:

```sh
uv run python make_trivia_countdown.py \
  "/path/to/source-video.mp4" \
  "/path/to/trivia.csv"
```

To choose the output location, add `--output`:

```sh
uv run python make_trivia_countdown.py \
  "/path/to/source-video.mp4" \
  "/path/to/trivia.csv" \
  --output "/path/to/finished-trivia.mp4"
```

To randomize the questions, use `--random`. Add a seed when you need to reproduce the same randomized order later:

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

Only complete questions that fit within the available time are used. The capacity is calculated as:

```text
available time = video duration - start delay - end-early time
time per question = question duration + answer duration
question capacity = available time rounded down to a whole number of questions
```

For example, a 90-second video with the defaults has 65 seconds available after the 10-second opening delay and 15-second ending reserve. Each question uses 12.5 seconds, so five complete questions fit. If the CSV contains more questions, the extra questions are not rendered. If all questions finish before the reserved ending, the source video continues without trivia panels.

During an answer reveal, the correct answer initially flashes and then remains highlighted. The final portion of the reveal crossfades into the next question. These effects do not add time to the question sequence.

## Command Reference

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
- An existing output file at the selected path is overwritten without confirmation.
- Generated overlay PNGs are temporary and deleted automatically unless `--overlay-dir` is used.

## Troubleshooting

### `brew: command not found`

Install Homebrew by following the instructions at [brew.sh](https://brew.sh/), then open a new Terminal window and run `brew install uv ffmpeg` again.

### `uv: command not found`

Run `brew install uv`. If Homebrew reports that `uv` is already installed, open a new Terminal window so its updated command path is loaded.

### `Required executable not found: ffmpeg` or `ffprobe`

Run `brew install ffmpeg`. The Homebrew FFmpeg package supplies both commands.

### `Video file does not exist` or `Trivia CSV does not exist`

Confirm the path and keep it in quotation marks if any folder or filename contains spaces. Dragging the file from Finder into Terminal is a reliable way to insert its full path.

### `Input video is too short to show even one full trivia question`

The video does not have enough time for one question after the opening and ending reserves. Use a longer video or reduce values such as `--start-delay`, `--end-early`, `--duration`, or `--answer-duration`.

For example, remove the opening and ending reserves with:

```sh
uv run python make_trivia_countdown.py \
  "/path/to/source-video.mp4" \
  "/path/to/trivia.csv" \
  --start-delay 0 \
  --end-early 0
```

### The CSV reports missing columns or an invalid row

Compare the header with the required column names and inspect the row number shown in the error. Every required field must be nonempty, and `correct_answer` must contain an integer from `1` to `4`.

### Text is too small or difficult to read

Question and answer text wraps and shrinks automatically, but unusually long text may still be difficult to read. Shorten the wording, render a brief test, or use `--overlay-dir preview_overlays` to inspect the generated PNG files.

### Rendering takes a long time

The complete source video is re-encoded. Long or high-resolution videos can take several minutes or more, particularly on older hardware. Closing other processor-intensive applications may help.

## Current Limitations

- macOS is the only currently supported and verified operating system.
- The panel colors, typography, and lower-screen layout are fixed and are not configurable from the command line.
- The layout is intended primarily for landscape video. Portrait and unusual aspect ratios may not produce an ideal composition.
- Text fitting is automatic, but very long wording may become too small for comfortable viewing.
- One source video and one trivia CSV are processed per command.
- The tool creates a finished video; it does not provide an interactive visual editor.

## Privacy and Responsible Use

The application performs trivia rendering and video composition on your computer and contains no upload or telemetry functionality. Dependency installation may contact Homebrew and Python package registries to download required software.

You are responsible for having permission to use and distribute the source video, audio, trivia questions, and any other input content. The project's software license does not grant rights to third-party media.

## Getting Help

If a problem is not covered above, include the following information when asking the project maintainer or community for help:

- The full command you ran, with sensitive paths removed if necessary
- The complete error message
- Your macOS version
- The output of `uv --version` and `ffmpeg -version`

Do not attach private videos or trivia files unless you are comfortable making them available to repository maintainers.

## License

Trivia Countdown is available under the [MIT License](LICENSE). The license applies to this project's software and documentation, not to videos or other content processed with it.
