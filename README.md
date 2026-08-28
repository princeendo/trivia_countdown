# Trivia Countdown

Create an MP4 trivia countdown by placing question and answer panels over an existing video. Each question appears for a configurable amount of time, then the correct answer is highlighted before the next question begins.

![Animated example showing a trivia question, answer reveal, and transition to the next question](assets/trivia-demo.gif)

Trivia Countdown runs locally on your Mac. It does not upload your video or trivia questions, and it does not modify the source video.

## Quick Start

Trivia Countdown is currently supported on macOS. You will need a source video, [Homebrew](https://brew.sh/), and access to the Terminal application. This repository includes sample trivia questions but does not include a source video.

1. On the [GitHub project page](https://github.com/princeendo/trivia_countdown), select **Code**, then **Download ZIP**, and extract the downloaded file.
2. Open the extracted project folder in Terminal.
3. Install the required tools and set up the project:

```sh
brew install uv ffmpeg
. ./setup_venv.sh
```

4. Replace the example path below with your source video and render the five-question sample:

```sh
uv run python make_trivia_countdown.py \
  "/Users/your-name/Movies/countdown.mp4" \
  sample_objects/sample_of_5_trivia_questions.csv
```

The output is created beside the source video as `countdown_trivia_countdown.mp4`. Rendering can take several minutes depending on the video's duration and resolution.

> **Important:** An existing output file is replaced without a confirmation prompt. Use `--output` to choose a different path when you need to preserve an earlier render.

For step-by-step setup instructions and common installation problems, see the [Installation Guide](docs/01-installation.md).

## Documentation

The documentation is organized as a sequence for new users:

1. [Installation](docs/01-installation.md): requirements, download, setup, and verification
2. [Preparing Trivia Questions](docs/02-preparing-trivia.md): CSV columns, examples, and spreadsheet export
3. [Usage and Command Reference](docs/03-usage-and-reference.md): rendering, timing, options, and output behavior
4. [Troubleshooting](docs/04-troubleshooting.md): solutions for common setup, input, and rendering problems
5. [Limitations, Privacy, and Support](docs/05-limitations-privacy-and-support.md): platform scope, responsible use, and requesting help

For a concise list of every command-line option, run:

```sh
uv run python make_trivia_countdown.py --help
```

## License

Trivia Countdown is available under the [MIT License](LICENSE). The license applies to this project's software and documentation, not to videos or other content processed with it.
