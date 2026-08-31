# Port Trivia Countdown to Windows

## Goal

Deliver a Windows version of Trivia Countdown that supports:

- Windows 10 and Windows 11 on x64 hardware.
- A packaged desktop GUI distributed with an EXE installer.
- The existing source/developer CLI through PowerShell.
- Bundled, pinned `ffmpeg.exe` and `ffprobe.exe` binaries.
- An unsigned preview release with checksums, provenance, and documented
  Microsoft Defender SmartScreen behavior.

The first Windows milestone does not include Windows ARM64, a separately
packaged CLI executable, Microsoft Store distribution, or Authenticode signing.
Those items may be reconsidered after the preview release is qualified.

## Current State

The Python render pipeline is largely platform-neutral. Windows-oriented
runtime, packaging, CI, and documentation changes are implemented, but require
the verification and release gates below before a Windows installer is shipped.

The most important confirmed incompatibilities are:

- FFconcat rendering passed the selected bundled FFmpeg path matrix on Windows
  for drive-letter, spaces, Unicode, apostrophes, relative overlays, UNC, and
  long paths.
- Frozen application, installer, GUI DPI, and live-installation behavior remain
  unverified on a separate supported Windows system.
- The static GPL FFmpeg redistribution is approved; its corresponding-source
  archive still needs to be produced and attached to a Windows release.

## Status Definitions

| Status | Meaning |
| --- | --- |
| `BACKLOG` | Identified but not ready or prioritized. |
| `READY` | Requirements and dependencies are clear; work can begin. |
| `IN_PROGRESS` | Implementation or investigation is active. |
| `BLOCKED` | Work cannot proceed until the named blocker is resolved. |
| `IN_REVIEW` | Implementation exists and awaits review or Windows verification. |
| `VERIFIED` | Acceptance criteria passed on the declared Windows target. |
| `DEFERRED` | Intentionally postponed with a rationale and revisit condition. |
| `NOT_APPLICABLE` | Explicitly excluded from the agreed scope. |

`VERIFIED` requires evidence from Windows. A merged change or a passing macOS
test is not sufficient.

## Priority Definitions

| Priority | Meaning |
| --- | --- |
| `P0` | Blocks building, launching, or completing the primary Windows workflow. |
| `P1` | Causes incorrect core behavior or failure in a common workflow. |
| `P2` | Affects diagnostics, developer workflow, edge cases, or significant UX. |
| `P3` | Low-impact portability polish. |

## Confirmed Decisions

| ID | Decision | Status | Notes |
| --- | --- | --- | --- |
| DEC-001 | Support Windows 10 and Windows 11 on x64 | `VERIFIED` | Product scope decision; runtime qualification is tracked separately. |
| DEC-002 | Deliver a packaged GUI and retain the source CLI | `VERIFIED` | A separate packaged CLI executable is out of scope for the first milestone. |
| DEC-003 | Distribute the application with an EXE installer | `VERIFIED` | Inno Setup 7.1.0 x64 is selected; implementation qualification is tracked separately. |
| DEC-004 | Bundle pinned FFmpeg and ffprobe binaries | `VERIFIED` | Gyan FFmpeg 9.0.1 Essentials is pinned and approved for redistribution; corresponding-source delivery is tracked by WIN-402. |
| DEC-005 | Publish the first Windows build as an unsigned preview | `VERIFIED` | Document SmartScreen warnings; do not advise users to disable security controls. |
| DEC-006 | Use PowerShell for Windows source instructions | `VERIFIED` | CMD-specific instructions are not required for the first milestone. |

## Open Decisions

| ID | Decision | Priority | Status | Blocker | Completion Criteria |
| --- | --- | --- | --- | --- | --- |
| DEC-101 | Select the installer implementation | `P0` | `VERIFIED` | None | Inno Setup 7.1.0 x64 is selected. |
| DEC-102 | Select a Windows FFmpeg binary supplier and pinned version | `P0` | `VERIFIED` | None | Gyan FFmpeg 9.0.1 Essentials and its archive hash are pinned and approved for redistribution. |
| DEC-103 | Select a redistributable regular and bold font | `P0` | `VERIFIED` | None | Noto Sans Regular and Bold from `notofonts/noto-fonts` revision `20bc5918912503bc1537a407a694738c33c048aa`, SIL OFL 1.1. |
| DEC-104 | Define the minimum supported Windows 10 release | `P1` | `VERIFIED` | None | Windows 10 22H2 x64. |
| DEC-105 | Define the live installer qualification environment | `P1` | `VERIFIED` | None | Install and test on a separate live Windows 10 22H2 or Windows 11 x64 system. VM images and pristine-system checks are not required. |

## Blocker Register

| ID | Blocker | Type | Status | Blocks | Resolution |
| --- | --- | --- | --- | --- | --- |
| BLK-001 | Windows FFmpeg corresponding-source archive is not yet produced | License/dependency | `OPEN` | WIN-402, WIN-503, WIN-505, release | Produce and attach the matching source archive for FFmpeg, x264, and other GPL-covered static components. |
| BLK-002 | No approved portable font or bundled font license | License/dependency | `RESOLVED` | WIN-402, release | Noto Sans Regular and Bold, plus the SIL OFL 1.1 license, are included under `assets/fonts/`. |
| BLK-003 | Installer implementation has not been selected | Decision | `RESOLVED` | None | Inno Setup 7.1.0 x64 is selected. |
| BLK-005 | Windows FFconcat behavior for UNC paths and long paths is unverified | Technical | `RESOLVED` | WIN-103 | The selected bundled FFmpeg build passed the UNC and long-path render matrix on Windows. |
| BLK-006 | Authenticode certificate is unavailable | Signing | `ACCEPTED` | Production release only | Does not block the unsigned preview; revisit after preview qualification. |

## Phase 1: Runtime Portability

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-101 | Resolve bundled Windows executable names | `P0` | `IN_REVIEW` | None | None | Frozen builds find `bin/ffmpeg.exe` and `bin/ffprobe.exe`; source mode continues to use `PATH`; macOS behavior is preserved. | Unit tests on Windows and macOS; frozen smoke test. |
| WIN-102 | Bundle and load portable fonts | `P0` | `IN_REVIEW` | None | DEC-103 | Regular and bold fonts load through `resource_path`; requested sizes are honored in source and frozen builds; font and license are packaged. | Font unit tests, image inspection, packaged smoke test. |
| WIN-103 | Make FFconcat path handling portable | `P0` | `IN_REVIEW` | BLK-005 | None | Manifest paths are absolute and valid for spaces, Unicode, apostrophes, drive-letter paths, relative overlay directories, and supported UNC paths. | Unit tests plus real FFmpeg path-matrix renders on Windows. |
| WIN-104 | Add Windows-safe subprocess behavior | `P1` | `IN_REVIEW` | None | WIN-101 | Packaged GUI renders do not open child console windows; ffprobe and FFmpeg diagnostics decode safely under Windows code pages; CLI behavior remains visible. | Source and frozen GUI tests on Windows. |
| WIN-105 | Report Windows filesystem and process failures cleanly | `P1` | `IN_REVIEW` | None | None | CLI converts expected `OSError` and `PermissionError` failures into actionable `error:` messages without tracebacks; GUI retains actionable messages. | Unit tests for locked output, denied output directory, and missing executables. |
| WIN-106 | Make terminal progress Windows-safe | `P2` | `IN_REVIEW` | None | None | ANSI erase sequences are used only on a capable interactive terminal; redirected output contains newline-delimited text without control sequences; `--no-progress` remains unchanged. | Unit tests and PowerShell redirection test. |
| WIN-107 | Handle missing Windows Tkinter cleanly | `P2` | `IN_REVIEW` | None | None | Missing `tkinter` or `_tkinter` produces the documented friendly launcher error. | Mocked launcher tests. |
| WIN-108 | Generate PowerShell CLI commands in the source GUI | `P1` | `IN_REVIEW` | None | DEC-006 | Generated commands safely quote Windows paths, spaces, apostrophes, and optional arguments and can be executed in PowerShell. | Unit tests and manual copy/run test. |
| WIN-109 | Verify Windows replacement and cleanup behavior | `P1` | `IN_REVIEW` | None | WIN-105 | A failed or cancelled render does not replace an existing output; partial files and temporary overlays are removed when possible; file-lock errors are actionable. | Integration tests for cancellation, overwrite, and locked files. |

## Phase 2: Windows Source Workflow

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-201 | Define the PowerShell setup workflow | `P1` | `IN_REVIEW` | None | DEC-006 | A clean checkout can be prepared with `uv sync --frozen` without activation; GUI, CLI, and tests have documented PowerShell commands. | Follow instructions from a clean Windows checkout. |
| WIN-202 | Decide whether a PowerShell setup helper is needed | `P2` | `IN_REVIEW` | None | WIN-201 | Either add a small `setup_venv.ps1` with tests or document why direct `uv` commands are the supported workflow. | Clean-checkout setup test. |
| WIN-203 | Make maintainer checks shell-neutral | `P1` | `IN_REVIEW` | None | None | Verification does not rely on POSIX wildcard expansion; the same commands work in PowerShell and CI. | Run compile, unit-test, and `--help` checks on Windows and macOS. |
| WIN-204 | Add cross-platform repository text rules | `P2` | `IN_REVIEW` | None | None | `.gitattributes` protects shell scripts from CRLF conversion while allowing Windows-native scripts to use appropriate line endings; Windows build artifacts remain ignored. | Fresh Windows checkout and repository status check. |

## Phase 3: Tests and Continuous Integration

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-301 | Remove Unix-only assumptions from unit tests | `P1` | `IN_REVIEW` | None | WIN-101, WIN-108 | Tests use portable temporary paths and assert platform-appropriate executable and command behavior. | Unit suite passes on Windows and macOS. |
| WIN-302 | Add a Windows path and filesystem test matrix | `P0` | `VERIFIED` | None | WIN-103, WIN-109 | Tests cover spaces, Unicode, apostrophes, relative paths, drive-letter paths, supported UNC paths, long paths, locked outputs, and overwrite safety. | Unit and FFmpeg integration suite on Windows. |
| WIN-303 | Add Windows source CI | `P0` | `VERIFIED` | None | WIN-203, WIN-301 | A pinned `windows-2022` job installs with `uv`, compiles sources, runs tests, and checks CLI help; failures block release packaging. | Successful GitHub Actions run. |
| WIN-304 | Qualify GUI layout and DPI behavior | `P1` | `IN_REVIEW` | None | WIN-102, WIN-104 | Main workflows remain usable at 100%, 125%, 150%, and 200% display scaling; preview and progress controls are visible; icon rendering is acceptable. | Manual live-system GUI checklist with recorded results. |
| WIN-305 | Preserve macOS behavior during the port | `P0` | `IN_REVIEW` | None | All runtime changes | Existing macOS source tests and package workflow continue to pass; Windows conditionals do not replace macOS behavior. | Existing macOS CI and targeted regression tests. |

### WIN-305 macOS Verification Evidence

- 2026-08-29 on Apple Silicon macOS: `uv run python -m compileall -q make_trivia_countdown.py make_trivia_countdown_gui.py trivia_countdown`, `uv run python -m unittest tests.test_app` (22 passed, 2 Windows-only tests skipped), and `uv run python make_trivia_countdown.py --help` passed.
- 2026-08-29 on Apple Silicon macOS: rebuilt pinned FFmpeg n8.0.1/x264 with `scripts/build_ffmpeg_macos.sh`, then built `Trivia-Countdown-0.1.0-macOS-arm64.dmg` with `scripts/build_macos_dmg.sh`.
- 2026-08-29 on Apple Silicon macOS: the app signature and DMG verified, and the bundled `ffmpeg` and `ffprobe` binaries reported FFmpeg n8.0.1 with `--enable-libx264`.

This task remains `IN_REVIEW`: the tracker requires Windows evidence before an implementation task may be marked `VERIFIED`.

### WIN-302 Windows Verification Evidence

- 2026-08-30 on Windows 10 Pro x64 (build 26200):
  `scripts/verify_win302.ps1` passed with pinned Gyan FFmpeg 9.0.1 Essentials.
- The run completed all 22 tests in `tests.test_app`, then reran the special-path,
  UNC, long-path, failed-overwrite, and locked-output cases individually without
  skips. The report is at
  `build/verification/WIN-302-20260830-211651.log` in the Windows verification
  workspace.
- The UNC render used the writable authenticated SMB path
  `\\localhost\C$\Users\white\AppData\Local\Temp\trivia-countdown-win302`.
  The long-path render used `C:\trivia-countdown-win302` with Windows long paths
  enabled and generated paths longer than 260 characters.

### WIN-303 Windows Verification Evidence

- 2026-08-31: GitHub Actions [Windows source checks run 33350479536](https://github.com/princeendo/trivia_countdown/actions/runs/33350479536)
  passed on the pinned `windows-2022` runner at commit `26d73fe9289099f474ee614ebb68c06e846b30b8`.
- The `source-checks` job completed `uv sync --frozen`, source compilation,
  `tests.test_app`, and `make_trivia_countdown.py --help` successfully.

## Phase 4: Dependencies and Packaging

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-401 | Acquire and verify pinned FFmpeg binaries | `P0` | `VERIFIED` | None | DEC-102 | `ffmpeg.exe` and `ffprobe.exe` are x64, pinned, hash-verified, free of unexpected runtime DLL dependencies, and provide `libx264` and AAC support. | Version/configuration checks and a real render. |
| WIN-402 | Package third-party licenses and corresponding sources | `P0` | `BLOCKED` | BLK-001 | WIN-102, WIN-401 | Installer includes applicable Python, Tcl/Tk, Pillow, PyInstaller, font, FFmpeg, and x264 notices; matching FFmpeg/x264 source is published with the release when required. | License review and installed-file inspection. |
| WIN-403 | Create a Windows PyInstaller specification | `P0` | `IN_REVIEW` | None | WIN-101, WIN-102, WIN-401 | Build produces a windowed x64 GUI application containing Python, Tcl/Tk, Pillow, fonts, licenses, `ffmpeg.exe`, and `ffprobe.exe`; the app runs without system Python or FFmpeg. | PyInstaller build and frozen smoke test. |
| WIN-404 | Create a Windows application icon | `P2` | `IN_REVIEW` | None | None | A multi-resolution `.ico` derived from `assets/app_icon.png` is embedded in the executable and installer. | Explorer, taskbar, and installed shortcut inspection. |
| WIN-405 | Add packaged-application smoke tests | `P0` | `IN_REVIEW` | None | WIN-403 | Smoke mode launches; bundled executables run; a short sample render succeeds with system FFmpeg removed from `PATH`; no child console flashes. | Automated package test plus manual GUI render. |

## Phase 5: Installer and Release Automation

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-501 | Build the EXE installer | `P0` | `IN_REVIEW` | None | DEC-101, WIN-402, WIN-403, WIN-404 | Installer uses per-user installation unless elevation is justified, creates expected shortcuts, includes notices, supports clean uninstall, and has deterministic artifact naming. | Install, upgrade, and uninstall tests on a live supported Windows system. |
| WIN-502 | Add Windows package CI | `P0` | `IN_REVIEW` | None | WIN-303, WIN-401, WIN-405, WIN-501 | A pinned Windows runner builds the application and installer, verifies hashes and bundled tools, smoke-tests the result, and uploads the complete artifact set. | Successful workflow artifact build. |
| WIN-503 | Add checksums and build provenance | `P1` | `BLOCKED` | BLK-001 | WIN-502 | Release output includes SHA-256 checksums and GitHub build provenance for the installer and corresponding source archive. | Checksum verification and `gh attestation verify`. |
| WIN-504 | Qualify the unsigned preview by live installation | `P0` | `IN_REVIEW` | None | WIN-501, WIN-502, WIN-503 | Installer, first launch, render, output playback, upgrade, and uninstall pass on a separate live Windows 10 22H2 or Windows 11 x64 system. | Signed-off live-installation checklist. |
| WIN-505 | Publish an unsigned Windows prerelease | `P0` | `READY` | None | WIN-504, WIN-601 | Draft prerelease includes installer, checksums, FFmpeg corresponding source, provenance, release notes, support caveats, and accurate SmartScreen guidance. | Download artifacts through a browser and repeat the live-installation smoke test. |
| WIN-506 | Define the signed-release follow-up | `P2` | `DEFERRED` | BLK-006 | Preview feedback | Document certificate ownership, secret storage, timestamping, signing order, and verification before promoting Windows builds beyond preview status. | Approved signing design and verified signed artifact. |

### WIN-401 Windows Verification Evidence

- 2026-08-30 on Windows 11 Pro x64 (build 26200):
  `scripts/fetch_windows_ffmpeg.ps1 -Force` verified the pinned Gyan FFmpeg
  9.0.1 Essentials archive hash, then verified `ffmpeg.exe` and `ffprobe.exe`
  hashes and their x64 PE machine type (`0x8664`). Cached executables receive
  the same hash and architecture checks before reuse.
- `ffmpeg -version` and `ffprobe -version` reported the pinned static build.
  The bundled `bin` directory contained only the two executables, with no DLLs.
- The bundled tools created a 12,378-byte MP4 with `libx264` video and AAC
  audio. The bundled `ffprobe` confirmed H.264 video and AAC audio streams.

## Phase 6: Documentation

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-601 | Update the README and user documentation | `P0` | `IN_REVIEW` | None | Finalized setup, packaging, and release behavior | `README.md` and every file under `docs/` accurately cover Windows installation, PowerShell usage, paths, SmartScreen, troubleshooting, supported systems, privacy, and release procedures without making macOS instructions ambiguous. | Follow all Windows instructions from a clean system; check every link and duplicated command. |
| WIN-602 | Update maintainer guidance | `P1` | `IN_REVIEW` | None | WIN-203, WIN-502 | `AGENTS.md` contains platform-neutral setup and verification commands and the Windows package/release checks. | Execute documented commands in PowerShell and macOS CI. |
| WIN-603 | Update third-party and source notices | `P0` | `BLOCKED` | BLK-001, BLK-002 | WIN-402 | `THIRD_PARTY_NOTICES.md` and packaging documentation describe both macOS and Windows artifacts, native Pillow libraries, bundled fonts, FFmpeg provenance, and corresponding source locations. | License review and artifact inspection. |

## Verification Gates

### Gate 1: Source Checks

- `uv sync --frozen` succeeds in PowerShell.
- Python sources compile with a shell-neutral command.
- Unit tests pass on Windows and macOS.
- `uv run python make_trivia_countdown.py --help` succeeds.
- Redirected progress output contains no terminal escape sequences.

### Gate 2: Source Integration

- Create a synthetic H.264 source video with the approved FFmpeg build.
- Render the sample CSV with audio and without audio.
- Exercise paths containing spaces, Unicode, and apostrophes.
- Exercise relative and absolute overlay directories.
- Exercise drive-letter paths and supported UNC and long paths.
- Verify cancellation, output replacement, locked-output errors, and cleanup.
- Use ffprobe to verify duration, dimensions, H.264 video, optional AAC audio,
  and a nonzero output size.

### Gate 3: GUI

- Select source video, trivia CSV, and output through file dialogs.
- Generate a preview and switch the selected question.
- Start, cancel, and complete renders.
- Confirm the packaged GUI does not open child console windows.
- Check layout at 100%, 125%, 150%, and 200% display scaling.
- Confirm the source GUI's generated PowerShell command runs successfully.

### Gate 4: Frozen Application and Installer

- Run the packaged smoke-test mode.
- Run bundled `ffmpeg.exe -version` and `ffprobe.exe -version`.
- Complete a real render with system Python and FFmpeg absent.
- Install and run from paths containing spaces and Unicode.
- Confirm font, icon, notice, and executable resources are present.
- Confirm install, upgrade, uninstall, and temporary-file cleanup behavior.

### Gate 5: Preview Release

- Pass Gates 1 through 4 on a separate live Windows 10 22H2 or Windows 11 x64 system.
- Verify SHA-256 checksums and GitHub build provenance.
- Confirm the installer contains no unexpected binaries or DLL dependencies.
- Confirm SmartScreen guidance describes the unsigned preview accurately and
  does not instruct users to disable Windows security features.
- Download the release artifact through a browser and repeat the primary user
  workflow before publishing.

## Release Definition of Done

The Windows preview is complete when:

- All `P0` tasks are `VERIFIED` or explicitly removed from scope.
- No open blocker affects source setup, rendering, packaging, installation,
  licensing, or live-system qualification.
- Source CLI and packaged GUI workflows pass on the separately tested Windows 10
  22H2 or Windows 11 x64 system.
- The installer works without preinstalled Python, uv, FFmpeg, or ffprobe.
- Bundled fonts produce readable, correctly scaled overlays.
- Rendering succeeds for the documented Windows path matrix.
- Existing macOS CI remains green.
- README, all documentation under `docs/`, maintainer instructions, and
  third-party notices agree with the shipped behavior.
- The prerelease includes the installer, checksums, provenance, required
  corresponding source, and support caveats.

## Recommended Execution Order

1. Complete DEC-101 through DEC-105 and close BLK-001.
2. Implement WIN-101 through WIN-109 and verify source rendering on Windows.
3. Complete the Windows source workflow and test/CI phases.
4. Acquire and validate FFmpeg, fonts, licenses, and corresponding sources.
5. Build and smoke-test the frozen application.
6. Build and test the installer and release automation.
7. Update all documentation against the final behavior.
8. Perform live-installation qualification and publish the unsigned prerelease.

## Progress Summary

| Category | Count |
| --- | ---: |
| Confirmed decisions | 11 |
| Open or in-progress decisions | 0 |
| Open or accepted blockers | 2 |
| `READY` tasks | 1 |
| `IN_PROGRESS` tasks | 0 |
| `IN_REVIEW` tasks | 24 |
| `BLOCKED` tasks | 3 |
| `DEFERRED` tasks | 1 |
| `VERIFIED` implementation tasks | 3 |

Update this summary whenever task statuses change. Do not mark implementation
tasks `VERIFIED` until their listed Windows verification has passed.
