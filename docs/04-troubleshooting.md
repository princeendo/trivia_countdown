# Troubleshooting

## macOS Says the App Cannot Be Opened

The current DMG is ad-hoc signed, but it is not signed with an Apple Developer ID or notarized by Apple. First confirm that you downloaded it from the project's official [GitHub Releases page](https://github.com/princeendo/trivia_countdown/releases) and, if possible, verify `SHA256SUMS`.

Attempt to open the app once, then open **System Settings > Privacy & Security**. In the Security section, select **Open Anyway** beside the Trivia Countdown message and confirm **Open**. The control only appears after a blocked launch attempt. Do not disable Gatekeeper globally.

If macOS reports that the app is damaged rather than identifying it as an unverified app, remove that copy, download the DMG again, and verify its checksum. Open an issue if a verified download still fails.

## The DMG or App Is Incompatible

The current download requires an Apple Silicon Mac running macOS 14 Sonoma or later. Choose **Apple menu > About This Mac** to check the chip and macOS version. Intel Macs are not supported by this prototype.

## `brew: command not found`

Homebrew is only required for a source installation. Normal DMG users should follow the [Mac app installation instructions](01-installation.md#install-the-mac-app). Source users can install Homebrew from [brew.sh](https://brew.sh/) and then run `brew install uv ffmpeg` again.

## `uv: command not found`

`uv` is only required for a source installation. Run `brew install uv`. If Homebrew reports that `uv` is already installed, open a new Terminal window so its updated command path is loaded.

On Windows source installations, install uv using the [official Windows instructions](https://docs.astral.sh/uv/getting-started/installation/) and open a new PowerShell window before retrying.

## `Required executable not found: ffmpeg` or `ffprobe`

This message should only occur in a source installation because the Mac app bundles both tools. macOS source users can run `brew install ffmpeg`. Windows source users must install an FFmpeg build that provides `ffmpeg.exe` and `ffprobe.exe` on `PATH`, then open a new PowerShell window. If the packaged app reports a missing bundled executable, reinstall it from a verified DMG and open an issue if the problem remains.

## The Desktop Interface Does Not Open

DMG users should first follow the [Mac app installation instructions](01-installation.md#install-the-mac-app) above. Source users can launch it from the project folder with `uv run python make_trivia_countdown_gui.py`.

If a macOS source launch opens a blank or black window, it is using an unsupported Tcl/Tk runtime. Run `. ./setup_venv.sh` to recreate the environment with the repository's Python 3.12 pin, then confirm `uv run python -c 'import tkinter; print(tkinter.TkVersion)'` prints `8.6` or newer. If setup reports that Tkinter is unavailable or too old, install a current Python distribution with Tcl/Tk 8.6 or later, remove `.venv`, and run the setup command again.

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

## The App Cannot Save the Output

The app creates missing output folders automatically. Confirm that you have permission to write to the selected location, choose a different location such as your Movies or Desktop folder if necessary, and make sure there is enough free disk space for a newly encoded copy of the source video.

## Requesting Help

If a problem is not covered above, see [Support Information](05-limitations-privacy-and-support.md#support-information) for what to include when requesting help. You can submit a report through the project's [GitHub Issues page](https://github.com/princeendo/trivia_countdown/issues).

---

[Previous: Usage and Command Reference](03-usage-and-reference.md) | [Back to README](../README.md) | [Next: Limitations, Privacy, and Support](05-limitations-privacy-and-support.md)
