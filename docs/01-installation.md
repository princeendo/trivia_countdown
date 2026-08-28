# Installation

The downloadable Trivia Countdown app supports Apple Silicon Macs running macOS 14 Sonoma or later. Intel Macs are not currently supported.

## Requirements

- An Apple Silicon Mac with macOS 14 or later
- A countdown or background video supported by the bundled FFmpeg tools, such as an MP4
- A CSV file containing trivia questions
- Enough free disk space for a newly encoded copy of the video

The DMG includes a sample trivia CSV but does not include a source video. You must provide the video that will appear behind the trivia panels.

## Install the Unsigned App

The current downloadable build is an unsigned preview. It is ad-hoc signed so it runs on Apple Silicon, but it is not signed with an Apple Developer ID or notarized by Apple. macOS therefore blocks its first launch even when the download is intact.

Only follow these steps for a DMG downloaded from the project's official [GitHub Releases page](https://github.com/princeendo/trivia_countdown/releases):

1. Download the latest file ending in `macOS-arm64.dmg`.
2. Optionally verify it against the release's `SHA256SUMS` file as described below.
3. Double-click the DMG to open it.
4. Drag **Trivia Countdown** onto the **Applications** shortcut.
5. Eject the **Trivia Countdown** disk image.
6. Open the Applications folder and double-click **Trivia Countdown**.
7. When macOS blocks the app, select **Done** or close the warning.
8. Open **System Settings > Privacy & Security**.
9. Scroll to the Security section, find the message stating that Trivia Countdown was blocked, and select **Open Anyway**.
10. Authenticate if macOS requests it, then confirm **Open**.

The override is saved for this copy of the app, so later launches should open normally. Do not disable Gatekeeper globally and do not run commands that remove quarantine from all downloads. These instructions use macOS's per-app security override.

If **Open Anyway** is missing, make sure you attempted to open the app immediately before visiting Privacy & Security. See [Troubleshooting](04-troubleshooting.md) for other launch problems.

## Verify the Download

Each GitHub release includes `SHA256SUMS`. Download the DMG, matching source archive, and `SHA256SUMS`. In Terminal, change to the folder containing all three files and run:

```sh
shasum -a 256 -c SHA256SUMS
```

The DMG and source archive should report `OK`. The checksum detects incomplete or altered downloads, but because it is hosted beside the app, it does not independently authenticate the publisher. GitHub also publishes build provenance for release artifacts. If you have the GitHub CLI installed, verify the DMG against this repository before overriding Gatekeeper:

```sh
gh attestation verify Trivia-Countdown-0.1.0-macOS-arm64.dmg --repo princeendo/trivia_countdown
```

Replace the filename with the version you downloaded. A valid attestation ties the artifact to this repository's GitHub Actions workflow and commit; it is not a substitute for Apple Developer ID signing.

## Open the App

After installation, launch **Trivia Countdown** from Applications. The app already contains Python, Tcl/Tk, Pillow, FFmpeg, and ffprobe. Normal app users do not need Homebrew, uv, Python, or Terminal.

The desktop window contains Main, Advanced, and Questions tabs. Choose a source video and CSV on Main, review the generated output path, and select **Create Video**.

## Install From Source

Developers who want the command-line interface or want to modify the project can run it from a source checkout. This path requires Homebrew and Terminal.

1. Download or clone the repository.
2. Open the project folder in Terminal.
3. Install uv and FFmpeg:

```sh
brew install uv ffmpeg
```

4. Set up the Python environment:

```sh
. ./setup_venv.sh
```

5. Launch the source GUI or inspect the command-line help:

```sh
uv run python make_trivia_countdown_gui.py
uv run python make_trivia_countdown.py --help
```

## Next Step

Prepare your own questions with [Preparing Trivia Questions](02-preparing-trivia.md), or use the sample from the mounted DMG or repository and continue to [Usage and Command Reference](03-usage-and-reference.md).

---

[Back to README](../README.md) | [Next: Preparing Trivia Questions](02-preparing-trivia.md)
