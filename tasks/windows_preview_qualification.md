# Windows Preview Qualification

**Status: NOT APPROVED FOR PUBLICATION.** A separate live Windows machine is
not currently available. Local automation and CI do not replace the checks below.
Keep the existing published `v0.1.0` release unchanged; use a new project version
and matching tag for the eventual Windows preview.

Copy this checklist into a qualification report and retain the completed report
with the release evidence. Do not tick a box without observing its result.
Use a separate live Windows 10 22H2 or Windows 11 x64 system; a VM or pristine
account is not required. Do not overwrite an existing installation without the
owner's approval. Never disable SmartScreen or other Windows security controls.

## Candidate Identity

Record before testing:

- Tester and date:
- Windows edition, version, build, and native architecture (`winver`):
- Display resolution and available scaling settings:
- Candidate version and Git commit:
- GitHub Actions build URL:
- Installer filename and SHA-256:
- Corresponding-source filename and SHA-256:
- SHA-256 checksum-file filename:
- Previous installed version (or “none”):

## Artifact and Source Review

- [ ] Download the installer, matching Windows FFmpeg source archive, and
  Windows checksum file from the successful workflow or draft prerelease.
  Download through a browser for the final check so Windows download-security
  behavior is exercised. GitHub's automatic repository source downloads are not
  the FFmpeg corresponding-source archive.
- [ ] Verify both SHA-256 entries using the PowerShell instructions in
  [Installation](../docs/01-installation.md#windows-preview-candidates).
- [ ] Verify GitHub provenance for **all three files** using
  `gh attestation verify '<filename>' --repo princeendo/trivia_countdown`.
  Record the workflow and commit reported by the verifier.
- [ ] Review the archive against
  [the source manifest and rebuild guide](../packaging/FFMPEG_WINDOWS_SOURCE_README.md).
  Confirm the pinned FFmpeg, x264, and zlib trees, actual build script,
  configurations, package/compiler inventory, and license/exception texts.
- [ ] Inspect installed `_internal\licenses\`, `_internal\THIRD_PARTY_NOTICES.md`,
  and `_internal\LICENSE`. Confirm Python, Tcl/Tk, Pillow/native-library,
  PyInstaller, Noto Sans, FFmpeg, x264, zlib, MinGW, and GCC runtime notices.
- [ ] Record the source/license reviewer's approval and any follow-up concerns.

## Install, Launch, and Render

- [ ] Launch the unsigned installer as a standard user. Record SmartScreen or
  antivirus messages and the decision made after verifying the download.
- [ ] Confirm per-user installation without an administrator prompt; check the
  default install directory and the optional desktop shortcut setting.
- [ ] Inspect the installer icon, Explorer executable icon, Start menu shortcut,
  optional desktop shortcut, and running application's taskbar icon.
- [ ] Open the installed app from its shortcut without system Python, uv,
  FFmpeg, or ffprobe on `PATH`. The packaged app has Main, Advanced, and Questions
  tabs, not the source-only CLI tab.
- [ ] Use file dialogs to choose a source video, the installed
  `Sample Trivia Questions.csv`, and an output path containing spaces and Unicode.
  Supply a video at least 90 seconds long for all five sample questions at defaults,
  or reduce the timing settings for a shorter video.
- [ ] Generate the preview, select another question, and toggle answer reveal.
  Confirm legible regular/bold fonts and correctly highlighted answers.
- [ ] Complete a render with source audio and one without audio. Observe the
  two progress bars and confirm no child console windows flash.
- [ ] Play the completed files in a normal Windows video player. Inspect the
  opening delay, question order, answer flashing/reveal, transitions, final
  frames, audio, duration, and readability. A successful FFmpeg decode alone is
  not human playback approval.
- [ ] Cancel during overlay generation and again during video composition.
  Confirm responsiveness, unchanged existing output, and no leftover partial
  MP4s or temporary overlay directories.
- [ ] Decline an overwrite prompt and confirm the existing output is unchanged.
  Then accept an overwrite and confirm only successful completion replaces it.
- [ ] Lock the output in another program and confirm a useful error, preserved
  original output, and successful retry after closing the other program.

## Display Scaling

At each setting below, restart the app if Windows requests it. Check Main,
Advanced, and Questions; file dialogs; question-table scrolling; preview;
progress; status messages; and Create/Cancel controls. No required control or
message should be clipped or unreachable. Record resolution and screenshots.
If a setting cannot be tested, leave its box empty and record the limitation.

- [ ] 100%
- [ ] 125%
- [ ] 150%
- [ ] 200%

## Upgrade, Uninstall, and Source Workflow

- [ ] Install a newer-version candidate over an older approved candidate. Record
  both versions/hashes, launch and render again, and confirm shortcuts and
  uninstall registration are correct. A same-version reinstall is insufficient.
- [ ] Uninstall through Windows Settings. Confirm app files, shortcuts, and
  uninstall registration are removed, while user videos/CSVs/outputs remain.
- [ ] Follow the documented source setup from a fresh checkout with
  `uv sync --frozen`, compilation, test discovery, and CLI help.
- [ ] In the source GUI, copy the CLI command and run it in PowerShell using
  paths with spaces, Unicode, and apostrophes. Confirm successful output and
  newline-delimited redirected progress without terminal escape sequences.

## Publication Approval

- [ ] Windows source and package CI and macOS regression CI passed for the
  candidate commit. Review skips; the local WIN-302 UNC/long-path report must
  qualify the same bundled FFmpeg build.
- [ ] All required checks above passed on the separate system. Attach reports,
  screenshots, hashes, build URLs, and human reviewer/tester sign-off.
- [ ] Reconcile `README.md`, every file under `docs/`, third-party notices, and
  [the Windows task tracker](port_to_windows.md). Do not advertise an installer
  as published before it is actually available.
- [ ] On a **new** matching version tag, inspect the draft prerelease containing
  the installer, Windows sources/checksums, provenance, and accurate unsigned
  preview caveats. A branch workflow run intentionally creates no release.
- [ ] Download the draft assets through a browser and repeat the primary
  install/launch/render/playback workflow against those exact files.
- [ ] Maintainer explicitly approves publication and publishes the prerelease.

Approval, date, exact approved installer hash, and remaining caveats:

**Pending.**
