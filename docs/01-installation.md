# Installation

This guide covers the supported macOS setup for Trivia Countdown. Other operating systems may work, but their setup and font rendering have not been verified.

## Requirements

- A Mac and access to the Terminal application
- A countdown or background video supported by FFmpeg, such as an MP4
- A CSV file containing trivia questions
- Enough free disk space for a newly encoded copy of the video

The repository includes a sample trivia CSV, but it does not include a source video. You must provide the video that will appear behind the trivia panels.

## 1. Download the Project

On the [Trivia Countdown GitHub page](https://github.com/princeendo/trivia_countdown), select **Code**, then **Download ZIP**. Open the downloaded ZIP file to extract the project folder.

## 2. Open the Project in Terminal

Open **Terminal** from **Applications > Utilities**. Type `cd `, including the space, drag the extracted project folder into the Terminal window, and press Return.

Your command will look similar to this:

```sh
cd /Users/your-name/Downloads/trivia_countdown-master
```

The remaining commands in this guide assume Terminal is open in this project folder.

## 3. Install the Required Tools

These instructions use [Homebrew](https://brew.sh/) to install `uv` and FFmpeg. If Homebrew is not already installed, follow the installation instructions on its official website first.

Run:

```sh
brew install uv ffmpeg
```

`uv` manages the Python environment and installs the Python package required by this project. FFmpeg and its companion tool, `ffprobe`, inspect and process the video.

## 4. Set Up the Python Environment

Run:

```sh
. ./setup_venv.sh
```

The script creates a local `.venv` environment, installs the project dependencies, and activates the environment in the current Terminal session.

You only need to repeat this setup after downloading a new copy of the project or when its dependencies change. The documented `uv run` commands work from a new Terminal session without manually activating `.venv` again.

## 5. Verify the Installation

Run:

```sh
uv run python make_trivia_countdown.py --help
```

You should see the available arguments and options. If the command fails, see [Troubleshooting](04-troubleshooting.md).

## Next Step

Prepare your own questions with [Preparing Trivia Questions](02-preparing-trivia.md), or use the included sample and continue directly to [Usage and Command Reference](03-usage-and-reference.md).

---

[Back to README](../README.md) | [Next: Preparing Trivia Questions](02-preparing-trivia.md)
