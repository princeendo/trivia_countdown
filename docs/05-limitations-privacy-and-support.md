# Limitations, Privacy, and Support

## Current Limitations

- The downloadable app supports Apple Silicon Macs running macOS 14 or later. Intel Macs and other operating systems are not currently supported.
- The current downloadable preview is ad-hoc signed, but is not signed with an Apple Developer ID or notarized, so macOS may require its per-app **Open Anyway** override on first launch.
- The panel colors, typography, and lower-screen layout are fixed and are not configurable from either the desktop interface or command line.
- The layout is intended primarily for landscape video. Portrait and unusual aspect ratios may not produce an ideal composition.
- Text fitting is automatic, but very long wording may become too small for comfortable viewing.
- One source video and one trivia CSV are processed per command.
- The GUI provides static frame-and-overlay previews and a read-only question inspector; it does not provide video playback, a timeline editor, or CSV editing.

## Privacy

The application performs trivia rendering and video composition on your computer and contains no upload or telemetry functionality. The downloadable app bundles its runtime dependencies and does not contact Homebrew or Python package registries. Source installation and release builds may contact those services and upstream source repositories. FFmpeg may copy supported source metadata into the generated video, so review the source file's metadata if that matters for your privacy.

## Responsible Use

You are responsible for having permission to use and distribute the source video, audio, trivia questions, and any other input content. The project's software license does not grant rights to third-party media.

Do not share private videos or trivia files when requesting help unless you are comfortable making them available to repository maintainers.

## Support Information

When asking the project maintainer or community for help, open a report on the project's [GitHub Issues page](https://github.com/princeendo/trivia_countdown/issues) and provide:

- Whether you installed the GitHub DMG or launched `make_trivia_countdown_gui.py` from source
- The complete error message
- Your macOS version
- Whether the Mac has an Apple Silicon or Intel processor
- The release version, or the DMG filename, and whether its SHA-256 checksum passed
- For source installations only, the output of `uv --version` and `ffmpeg -version`

Start with the [Troubleshooting Guide](04-troubleshooting.md), which covers the most common setup, input, and rendering problems.

## License

Trivia Countdown is available under the [MIT License](../LICENSE). The license applies to this project's software and documentation, not to videos or other content processed with it.

The downloadable app also contains separate FFmpeg and x264 executables distributed under the GNU General Public License. Their notices and the location of exact corresponding source code are documented in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

---

[Previous: Troubleshooting](04-troubleshooting.md) | [Back to README](../README.md)
