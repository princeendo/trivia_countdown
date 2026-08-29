# Installation

The downloadable Trivia Countdown app is the recommended installation for normal users. It supports Apple Silicon Macs running macOS 14 Sonoma or later. Intel Macs are not currently supported.

## Requirements

- An Apple Silicon Mac with macOS 14 or later
- A countdown or background video supported by the bundled FFmpeg tools, such as an MP4
- A CSV file containing trivia questions
- Enough free disk space for a newly encoded copy of the video

The DMG includes a sample trivia CSV but does not include a source video. You must provide the video that will appear behind the trivia panels.

## Install the Mac App

The current downloadable build is an ad-hoc-signed preview. It is not signed with an Apple Developer ID or notarized by Apple, so macOS may block the first launch of a quarantined download. The ad-hoc signature does not authenticate the publisher, and notarization has not been performed.

Only follow these steps for a DMG downloaded from the project's official [GitHub Releases page](https://github.com/princeendo/trivia_countdown/releases):

1. Download the latest `Trivia-Countdown-<version>-macOS-arm64.dmg` file.
2. Optionally verify it against the release's `SHA256SUMS` file as described below.
3. Double-click the DMG to open it.
4. Drag **Trivia Countdown** onto the **Applications** shortcut.
5. If you want to try the included sample, drag **Sample Trivia Questions.csv** to your Desktop or Documents folder.
6. Eject the **Trivia Countdown** disk image.
7. Open the Applications folder and double-click **Trivia Countdown**.
8. When macOS blocks the app, select **Done** or close the warning.
9. Open **System Settings > Privacy & Security**.
10. Scroll to the Security section, find the message stating that Trivia Countdown was blocked, and select **Open Anyway**.
11. Authenticate if macOS requests it, then confirm **Open**.

The override is saved for this copy of the app, so later launches should open normally. Do not disable Gatekeeper globally and do not run commands that remove quarantine from all downloads. These instructions use macOS's per-app security override.

If **Open Anyway** is missing, make sure you attempted to open the app immediately before visiting Privacy & Security. See [Troubleshooting](04-troubleshooting.md) for other launch problems.

## Verify the Download

Each GitHub release includes `SHA256SUMS`. For a complete release verification, download the DMG, the matching `Trivia-Countdown-FFmpeg-<ffmpeg-version>-sources.tar.gz` asset, and `SHA256SUMS`. Do not use GitHub's automatically generated **Source code (zip)** or **Source code (tar.gz)** downloads; those are different files. In Terminal, change to the folder containing all three release assets and run:

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

This is an advanced alternative for developers who want the command-line interface, want to modify the project, or cannot use the packaged Apple Silicon app. It requires Python 3.9 or later with Tcl/Tk support, uv, and FFmpeg. The downloadable app remains Mac-only until the Windows preview passes its separate qualification process.

### macOS

1. Download or clone the repository.
2. Open the project folder in Terminal.
3. Install uv and FFmpeg:

```sh
brew install uv ffmpeg
```

4. Set up the Python environment. The setup script creates or updates the project's `.venv`:

```sh
. ./setup_venv.sh
```

5. Confirm that the selected Python includes Tkinter:

```sh
uv run python -c 'import tkinter; print(tkinter.TkVersion)'
```

If this fails with `tkinter` or `_tkinter` unavailable, install a Python distribution with Tcl/Tk support, remove `.venv`, and repeat steps 4 and 5 so uv creates the environment with that Python.

6. Launch the source GUI or inspect the command-line help:

```sh
uv run python make_trivia_countdown_gui.py
uv run python make_trivia_countdown.py --help
```

### Windows PowerShell

The Windows source workflow targets Windows 10 22H2 and Windows 11 on x64 hardware. It is intended for developers while the packaged Windows preview is being qualified.

1. Download or clone the repository, then open its folder in PowerShell.
2. Install Python with Tcl/Tk support, [uv](https://docs.astral.sh/uv/getting-started/installation/), and an FFmpeg build that provides `ffmpeg.exe` and `ffprobe.exe` on `PATH`.
3. Create the locked environment without activating it:

```powershell
uv sync --frozen
```

4. Confirm Tkinter is available:

```powershell
uv run python -c "import tkinter; print(tkinter.TkVersion)"
```

If this reports that `tkinter` or `_tkinter` is unavailable, install a Python distribution that includes Tcl/Tk, remove `.venv`, and repeat the setup command.

5. Launch the source GUI or inspect the command-line help:

```powershell
uv run python make_trivia_countdown_gui.py
uv run python make_trivia_countdown.py --help
```

## Next Step

Prepare your own questions with [Preparing Trivia Questions](02-preparing-trivia.md), or use the sample CSV you copied from the DMG, and continue to [Usage and Command Reference](03-usage-and-reference.md).

---

[Back to README](../README.md) | [Next: Preparing Trivia Questions](02-preparing-trivia.md)
