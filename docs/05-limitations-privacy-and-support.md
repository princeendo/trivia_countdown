# Limitations, Privacy, and Support

## Current Limitations

- macOS is the only currently supported and verified operating system.
- The panel colors, typography, and lower-screen layout are fixed and are not configurable from the command line.
- The layout is intended primarily for landscape video. Portrait and unusual aspect ratios may not produce an ideal composition.
- Text fitting is automatic, but very long wording may become too small for comfortable viewing.
- One source video and one trivia CSV are processed per command.
- The GUI provides static frame-and-overlay previews and a read-only question inspector; it does not provide video playback, a timeline editor, or CSV editing.

## Privacy

The application performs trivia rendering and video composition on your computer and contains no upload or telemetry functionality. Dependency installation may contact Homebrew and Python package registries to download required software.

## Responsible Use

You are responsible for having permission to use and distribute the source video, audio, trivia questions, and any other input content. The project's software license does not grant rights to third-party media.

Do not share private videos or trivia files when requesting help unless you are comfortable making them available to repository maintainers.

## Support Information

When asking the project maintainer or community for help, provide:

- The full command you ran, with sensitive paths removed if necessary, or that you launched `make_trivia_countdown_gui.py`
- The complete error message
- Your macOS version
- The output of `uv --version` and `ffmpeg -version`

Start with the [Troubleshooting Guide](04-troubleshooting.md), which covers the most common setup, input, and rendering problems.

## License

Trivia Countdown is available under the [MIT License](../LICENSE). The license applies to this project's software and documentation, not to videos or other content processed with it.

---

[Previous: Troubleshooting](04-troubleshooting.md) | [Back to README](../README.md)
