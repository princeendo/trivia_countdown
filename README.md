# Trivia Countdown

Create an MP4 trivia countdown by placing question and answer panels over an existing video. Each question appears for a configurable amount of time, then the correct answer is highlighted before the next question begins.

![Animated example showing a trivia question, answer reveal, and transition to the next question](assets/trivia-demo.gif)

The currently downloadable app runs locally on your Mac. It does not upload your video or trivia questions, and it does not modify the source video.

## Quick Start: Mac App

The downloadable app is the recommended way for non-technical users to create a video. It supports Apple Silicon Macs running macOS 14 Sonoma or later. You need a source video and a trivia CSV; the DMG includes a sample CSV but does not include a source video.

1. Open the [GitHub Releases page](https://github.com/princeendo/trivia_countdown/releases) and download the latest `Trivia-Countdown-<version>-macOS-arm64.dmg` file.
2. Open the DMG and drag **Trivia Countdown** into the **Applications** shortcut.
3. Before ejecting the DMG, drag **Sample Trivia Questions.csv** to your Desktop or Documents folder if you want to try the sample.
4. Eject the disk image and open **Trivia Countdown** from Applications.
5. If macOS blocks the first launch, open **System Settings > Privacy & Security**, select **Open Anyway** beside Trivia Countdown, then confirm **Open**.
6. In the app, choose your source video and trivia CSV, confirm the output path, and select **Create Video**.

The preview build is ad-hoc signed, but it is not signed with an Apple Developer ID or notarized by Apple. macOS may therefore block the first launch of the downloaded app. Only use **Open Anyway** for a DMG downloaded from this repository's Releases page. Do not disable Gatekeeper globally. See the [Installation Guide](docs/01-installation.md) for complete steps and checksum verification.

The Main tab shows a static source-video frame with the selected trivia overlay and separate progress bars for overlay generation and video composition. Use **Advanced** to change timing defaults and **Questions** to inspect the CSV, 25 questions per page, and select the previewed question. **Previous** and **Next** browse the full collection while keeping the table's widget count bounded. The GUI confirms before replacing an existing file, supports cancellation, and replaces the selected output only after a successful render.

## For Developers

Developers can run the GUI or command line from a source checkout on macOS or Windows. The repository pins its uv environment to Python 3.12; this advanced path also requires Tcl/Tk support and FFmpeg. See the [source installation instructions](docs/01-installation.md#install-from-source).

The source GUI includes a **CLI** tab that generates the equivalent command. The packaged app does not include this developer-only tab.

## Documentation

Start with the path that matches your role:

### Mac app users

1. [Installation](docs/01-installation.md): download the app and handle the first launch
2. [Preparing Trivia Questions](docs/02-preparing-trivia.md): create or validate a CSV
3. [Usage and Command Reference](docs/03-usage-and-reference.md): use the GUI and understand its settings
4. [Troubleshooting](docs/04-troubleshooting.md): solve common setup, input, and rendering problems
5. [Limitations, Privacy, and Support](docs/05-limitations-privacy-and-support.md): platform scope, responsible use, and requesting help

### Source and CLI users

Use [Installation](docs/01-installation.md#install-from-source) for setup and [Usage and Command Reference](docs/03-usage-and-reference.md#command-line) for command-line options.

### Maintainers

The [Distribution and Release Roadmap](tasks/distribution_and_release.md) tracks the next release from `master`, optional Homebrew installation, Microsoft Store packaging/submissions, and an installation website. Its manually triggered Microsoft Store connection check is read-only and does not submit or publish an app. Mac Developer ID signing and notarization are deferred; the roadmap records planned channels, not additional downloads already available.

Use [Building and Releasing](docs/06-building-and-releasing.md) for unsigned DMG artifacts, Windows installer candidates and frozen-render checks, and GitHub prereleases. The Windows installer bundles source-built FFmpeg and ffprobe; end users will not install them separately. The build also generates the matching source archive. Windows publication remains gated on source/license review, build provenance, and the [separate live-installation qualification checklist](tasks/windows_preview_qualification.md). Branch builds do not publish releases; matching new version tags prepare draft prereleases only.

Windows candidate testers: GitHub Actions downloads the `trivia-countdown-windows-x64` artifact as a ZIP. Extract it and run `Trivia-Countdown-<version>-Windows-x64-Setup.exe`, the installer. The inner `Trivia Countdown.exe` in a raw application folder launches the app directly. See [Windows candidate installation](docs/01-installation.md#windows-preview-candidates).

For a concise list of every command-line option, source users can run:

```sh
uv run python make_trivia_countdown.py --help
```

## Sample Trivia

The source checkout includes a [master Bible and church-trivia collection](sample_objects/master_trivia.csv), [23-question sets](sample_objects/sets/), and a separate remainder file. The collection includes 100 new questions reviewed against the original batches. See the [sample collection guide](sample_objects/README.md) for counts, source references, and usage.

## License

Trivia Countdown is available under the [MIT License](LICENSE). The license applies to this project's software and documentation, not to videos or other content processed with it.
