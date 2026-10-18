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

- FFconcat rendering passed the Windows path matrix again with the source-built
  replacement, including UNC and long paths.
- Local frozen application preview and render checks pass on Windows 11 x64.
  Installer, GUI DPI, and separate live-installation behavior remain unverified.
- The approved path now builds FFmpeg/x264/zlib from pinned sources, bundles the
  executables, and generates the matching source archive. Source/license review,
  provenance, and live-system qualification remain release gates.

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
| DEC-004 | Bundle pinned FFmpeg and ffprobe binaries | `VERIFIED` | Self-build FFmpeg 9.0.1, x264, and zlib from exact commits; ship both executables in the installer and the matching source archive beside it. User approved this path on 2026-10-17. |
| DEC-005 | Publish the first Windows build as an unsigned preview | `VERIFIED` | Document SmartScreen warnings; do not advise users to disable security controls. |
| DEC-006 | Use PowerShell for Windows source instructions | `VERIFIED` | CMD-specific instructions are not required for the first milestone. |

## Open Decisions

| ID | Decision | Priority | Status | Blocker | Completion Criteria |
| --- | --- | --- | --- | --- | --- |
| DEC-101 | Select the installer implementation | `P0` | `VERIFIED` | None | Inno Setup 7.1.0 x64 is selected. |
| DEC-102 | Select a Windows FFmpeg build and pinned version | `P0` | `VERIFIED` | None | Build FFmpeg 9.0.1, x264, and zlib from the commits in `scripts/build_ffmpeg_windows.sh`; disable external-library autodetection and retain matching sources/build instructions. Replaces Gyan Essentials. |
| DEC-103 | Select a redistributable regular and bold font | `P0` | `VERIFIED` | None | Noto Sans Regular and Bold from `notofonts/noto-fonts` revision `20bc5918912503bc1537a407a694738c33c048aa`, SIL OFL 1.1. |
| DEC-104 | Define the minimum supported Windows 10 release | `P1` | `VERIFIED` | None | Windows 10 22H2 x64. |
| DEC-105 | Define the live installer qualification environment | `P1` | `VERIFIED` | None | Install and test on a separate live Windows 10 22H2 or Windows 11 x64 system. VM images and pristine-system checks are not required. |

## Blocker Register

| ID | Blocker | Type | Status | Blocks | Resolution |
| --- | --- | --- | --- | --- | --- |
| BLK-001 | Windows FFmpeg corresponding-source archive is not yet produced | License/dependency | `RESOLVED` | None | Replaced the opaque supplier bundle with a source-pinned FFmpeg/x264/zlib build that generates matching sources, build instructions, configurations, and licenses. Release review, attachment, and provenance remain WIN-402/WIN-503 gates. |
| BLK-002 | No approved portable font or bundled font license | License/dependency | `RESOLVED` | WIN-402, release | Noto Sans Regular and Bold, plus the SIL OFL 1.1 license, are included under `assets/fonts/`. |
| BLK-003 | Installer implementation has not been selected | Decision | `RESOLVED` | None | Inno Setup 7.1.0 x64 is selected. |
| BLK-005 | Windows FFconcat behavior for UNC paths and long paths is unverified | Technical | `RESOLVED` | WIN-103 | The selected bundled FFmpeg build passed the UNC and long-path render matrix on Windows. |
| BLK-006 | Authenticode certificate is unavailable | Signing | `ACCEPTED` | Production release only | Does not block the unsigned preview; revisit after preview qualification. |
| BLK-007 | Separate live Windows qualification system is unavailable | Test environment | `OPEN` | WIN-304, WIN-504, WIN-505, release | User confirmed on 2026-10-17 that another live Windows x64 machine is not available. Keep the candidate unpublished; complete [the qualification checklist](windows_preview_qualification.md) when a system is available. |

## Phase 1: Runtime Portability

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-101 | Resolve bundled Windows executable names | `P0` | `VERIFIED` | None | None | Frozen builds find `bin/ffmpeg.exe` and `bin/ffprobe.exe`; source mode continues to use `PATH`; macOS behavior is preserved. | Windows source/frozen renders and macOS source/package CI passed on 2026-10-17. |
| WIN-102 | Bundle and load portable fonts | `P0` | `IN_REVIEW` | None | DEC-103 | Regular and bold fonts load through `resource_path`; requested sizes are honored in source and frozen builds; font and license are packaged. | Font unit tests, image inspection, packaged smoke test. |
| WIN-103 | Make FFconcat path handling portable | `P0` | `VERIFIED` | None | None | Manifest paths are absolute and valid for spaces, Unicode, apostrophes, drive-letter paths, relative overlay directories, and supported UNC paths. | Unit tests plus real FFmpeg path-matrix renders on Windows; source-built bundle requalified on 2026-10-17. |
| WIN-104 | Add Windows-safe subprocess behavior | `P1` | `IN_REVIEW` | None | WIN-101 | Packaged GUI renders do not open child console windows; ffprobe and FFmpeg diagnostics decode safely under Windows code pages; CLI behavior remains visible. | Source and frozen GUI tests on Windows. |
| WIN-105 | Report Windows filesystem and process failures cleanly | `P1` | `VERIFIED` | None | None | CLI converts expected `OSError` and `PermissionError` failures into actionable `error:` messages without tracebacks; GUI retains actionable messages. | Windows unit tests cover CLI preparation/render errors, missing executable errors, and locked-output preservation. |
| WIN-106 | Make terminal progress Windows-safe | `P2` | `VERIFIED` | None | None | ANSI erase sequences are used only on a capable interactive terminal; redirected output contains newline-delimited text without control sequences; `--no-progress` remains unchanged. | Windows unit tests and real PowerShell command render with redirected progress passed on 2026-10-17. |
| WIN-107 | Handle missing Windows Tkinter cleanly | `P2` | `VERIFIED` | None | None | Missing `tkinter` or `_tkinter` produces the documented friendly launcher error. | Mocked launcher tests passed on Windows for both missing modules and unrelated import-error propagation. |
| WIN-108 | Generate PowerShell CLI commands in the source GUI | `P1` | `IN_REVIEW` | None | DEC-006 | Generated commands safely quote Windows paths, spaces, apostrophes, and optional arguments and can be executed in PowerShell. | Unit tests and manual copy/run test. |
| WIN-109 | Verify Windows replacement and cleanup behavior | `P1` | `VERIFIED` | None | WIN-105 | A failed or cancelled render does not replace an existing output; partial files and temporary overlays are removed when possible; file-lock errors are actionable. | Real Windows FFmpeg cancellation, locked-handle failure, successful overwrite/retry, and temporary-file cleanup tests passed; unit tests cover failed composition and cancellation at FFmpeg exit. |

## Phase 2: Windows Source Workflow

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-201 | Define the PowerShell setup workflow | `P1` | `VERIFIED` | None | DEC-006 | A clean checkout can be prepared with `uv sync --frozen` without activation; GUI, CLI, and tests have documented PowerShell commands. | Fresh local Windows clone passed sync, Tkinter check, compilation, all 40 then-current tests without skips, GUI startup, and CLI help on 2026-10-17. |
| WIN-202 | Decide whether a PowerShell setup helper is needed | `P2` | `VERIFIED` | None | WIN-201 | Either add a small `setup_venv.ps1` with tests or document why direct `uv` commands are the supported workflow. | Documented direct locked `uv` setup without activation or execution-policy changes; verified in a fresh Windows clone. |
| WIN-203 | Make maintainer checks shell-neutral | `P1` | `VERIFIED` | None | None | Verification does not rely on POSIX wildcard expansion; the same commands work in PowerShell and CI. | Compile, full test discovery, and CLI help passed in Windows and macOS CI plus a fresh local Windows clone. |
| WIN-204 | Add cross-platform repository text rules | `P2` | `VERIFIED` | None | None | `.gitattributes` protects shell scripts from CRLF conversion while allowing Windows-native scripts to use appropriate line endings; Windows build artifacts remain ignored. | Fresh Windows clone retained LF shell scripts and a clean working tree after setup/GUI/tests on 2026-10-17. |

## Phase 3: Tests and Continuous Integration

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-301 | Remove Unix-only assumptions from unit tests | `P1` | `VERIFIED` | None | WIN-101, WIN-108 | Tests use portable temporary paths and assert platform-appropriate executable and command behavior. | Full discovery passed on Windows and macOS, with only platform/tool-availability skips in CI; all configured local Windows cases passed. |
| WIN-302 | Add a Windows path and filesystem test matrix | `P0` | `VERIFIED` | None | WIN-103, WIN-109 | Tests cover spaces, Unicode, apostrophes, relative paths, drive-letter paths, supported UNC paths, long paths, locked outputs, and overwrite safety. | Unit and FFmpeg integration suite on Windows. |
| WIN-303 | Add Windows source CI | `P0` | `VERIFIED` | None | WIN-203, WIN-301 | A pinned `windows-2022` job installs with `uv`, compiles sources, runs tests, and checks CLI help; failures block release packaging. | Successful GitHub Actions run. |
| WIN-304 | Qualify GUI layout and DPI behavior | `P1` | `BLOCKED` | BLK-007 | WIN-102, WIN-104 | Main workflows remain usable at 100%, 125%, 150%, and 200% display scaling; preview and progress controls are visible; icon rendering is acceptable. | Manual live-system GUI checklist with recorded results. |
| WIN-305 | Preserve macOS behavior during the port | `P0` | `VERIFIED` | None | All runtime changes | Existing macOS source tests and package workflow continue to pass; Windows conditionals do not replace macOS behavior. | macOS source/bundled-tool tests, app/DMG build, frozen smoke, codesign, checksums, and provenance passed on 2026-10-17. |

### WIN-305 macOS Verification Evidence

- 2026-08-29 on Apple Silicon macOS: `uv run python -m compileall -q make_trivia_countdown.py make_trivia_countdown_gui.py trivia_countdown`, `uv run python -m unittest tests.test_app` (22 passed, 2 Windows-only tests skipped), and `uv run python make_trivia_countdown.py --help` passed.
- 2026-08-29 on Apple Silicon macOS: rebuilt pinned FFmpeg n8.0.1/x264 with `scripts/build_ffmpeg_macos.sh`, then built `Trivia-Countdown-0.1.0-macOS-arm64.dmg` with `scripts/build_macos_dmg.sh`.
- 2026-08-29 on Apple Silicon macOS: the app signature and DMG verified, and the bundled `ffmpeg` and `ffprobe` binaries reported FFmpeg n8.0.1 with `--enable-libx264`.

The earlier macOS-only evidence was insufficient by itself. Windows source and
frozen renders now pass too. On 2026-10-17,
[macOS run 39094570423](https://github.com/princeendo/trivia_countdown/actions/runs/39094570423)
passed at `bce7b8b298d9ce870dd922b820b23cf9eee5f73e`: 40 discovered tests before
and after building the pinned media tools (eight initial availability/platform
skips; five Windows-only skips with bundled tools), app/DMG construction,
frozen startup, media-tool versions, signature/DMG verification, and checksums.
Downloaded all three macOS artifacts and independently verified checksums and
GitHub provenance constrained to this repository, workflow, commit, branch,
and GitHub-hosted runners. Evidence is under
`build/verification/ci-macos-39094570423/` and
`build/verification/macOS-39094570423-*-attestation.json`. No release was created.

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
| WIN-401 | Build and verify source-pinned FFmpeg binaries | `P0` | `VERIFIED` | None | DEC-102 | `ffmpeg.exe` and `ffprobe.exe` are x64, source-pinned, hash-verified on cache reuse, free of unexpected runtime DLL dependencies, and provide `libx264` and AAC support. | Version/configuration checks and a real render. |
| WIN-402 | Package third-party licenses and corresponding sources | `P0` | `IN_REVIEW` | None | WIN-102, WIN-401 | Installer includes applicable Python, Tcl/Tk, Pillow, PyInstaller, font, FFmpeg, x264, zlib, and compiler-runtime notices; matching sources/build instructions are published with the release. | License review and installed-file inspection. |
| WIN-403 | Create a Windows PyInstaller specification | `P0` | `VERIFIED` | None | WIN-101, WIN-102, WIN-401 | Build produces a windowed x64 GUI application containing Python, Tcl/Tk, Pillow, fonts, licenses, `ffmpeg.exe`, and `ffprobe.exe`; the app runs without system Python or FFmpeg. | PyInstaller build and frozen smoke test. |
| WIN-404 | Create a Windows application icon | `P2` | `IN_REVIEW` | None | None | A multi-resolution `.ico` derived from `assets/app_icon.png` is embedded in the executable and installer. | Explorer, taskbar, and installed shortcut inspection. |
| WIN-405 | Add packaged-application smoke tests | `P0` | `IN_REVIEW` | None | WIN-403 | Smoke mode launches; bundled executables run; a short sample render succeeds with system FFmpeg removed from `PATH`; no child console flashes. | Automated package test plus manual GUI render. |

## Phase 5: Installer and Release Automation

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-501 | Build the EXE installer | `P0` | `IN_REVIEW` | None | DEC-101, WIN-402, WIN-403, WIN-404 | Installer uses per-user installation unless elevation is justified, creates expected shortcuts, includes notices, supports clean uninstall, and has deterministic artifact naming. | Install, upgrade, and uninstall tests on a live supported Windows system. |
| WIN-502 | Add Windows package CI | `P0` | `IN_REVIEW` | None | WIN-303, WIN-401, WIN-405, WIN-501 | A pinned Windows runner builds the application and installer, verifies hashes and bundled tools, smoke-tests the result, and uploads the complete artifact set including matching sources. | Successful workflow artifact build; rerun after the self-built FFmpeg switch. |
| WIN-503 | Add checksums and build provenance | `P1` | `IN_REVIEW` | None | WIN-502 | Release output includes SHA-256 checksums and GitHub build provenance for the installer and corresponding source archive. | Checksum verification and `gh attestation verify` after a new CI build. |
| WIN-504 | Qualify the unsigned preview by live installation | `P0` | `BLOCKED` | BLK-007 | WIN-501, WIN-502, WIN-503 | Installer, first launch, render, output playback, upgrade, and uninstall pass on a separate live Windows 10 22H2 or Windows 11 x64 system. | Signed-off live-installation checklist. |
| WIN-505 | Publish an unsigned Windows prerelease | `P0` | `BLOCKED` | BLK-007 | WIN-504, WIN-601 | Draft prerelease includes installer, checksums, FFmpeg corresponding source, provenance, release notes, support caveats, and accurate SmartScreen guidance. | Download artifacts through a browser and repeat the live-installation smoke test. |
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

### WIN-502 Windows Verification Evidence

- 2026-08-31: GitHub Actions [Build unsigned Windows installer run 33351542983](https://github.com/princeendo/trivia_countdown/actions/runs/33351542983)
  passed on the pinned `windows-2022` runner at commit
  `0548ad765ca2459686ba9192468c22417db6d182`.
- The job installed hash-verified Inno Setup 7.1.0, built the PyInstaller GUI
  and installer, ran packaged GUI smoke mode plus bundled `ffmpeg.exe` and
  `ffprobe.exe`, verified the SHA-256 checksum, attested both release
  artifacts, and uploaded the `trivia-countdown-windows-x64` artifact.
- The downloaded installer SHA-256 matched
  `Trivia-Countdown-0.1.0-Windows-x64-SHA256SUMS.txt`, and
  `gh attestation verify` passed for the installer and checksum file.

### WIN-403 / WIN-405 Local Frozen-Application Evidence

- 2026-10-17 on Windows 11 Pro x64, build 26200: built the windowed application
  with Python 3.12.14, PyInstaller 6.22.2, and the hash-verified pinned Gyan
  FFmpeg 9.0.1 Essentials tools. Runtime licenses and fonts were collected into
  the package. This local Python version differs from CI's 3.12.10 pin.
- `scripts/verify_windows_package.ps1` passed with system Python and FFmpeg
  unavailable on the child process's `PATH` and Python environment overrides
  cleared. The application launched from outside the source directory,
  constructed its GUI, extracted preview frames, and rendered both silent
  and AAC-audio inputs using spaces, Unicode, and apostrophes in paths.
- Both three-second outputs had 640x360 H.264 video, the expected audio stream
  presence, nonzero size, and passed full FFmpeg decoding. Report:
  `build/verification/WIN-405-20261017-165229-4da529d453834b63a8b494da77ce1a37.json`.
- Repeated the checks after copying the complete package into a temporary
  application location containing Unicode, spaces, and an apostrophe. Report:
  `build/verification/WIN-405-20261017-165243-f63223f96fb64cde9bd68c065c130839.json`.
  The copied application and synthetic videos were removed after verification.
- Source compilation, CLI help, and test discovery passed: 33 tests ran, with
  only the unconfigured UNC and long-path cases skipped. Their earlier WIN-302
  qualification is retained above; those two cases were not requalified here.
- A negative check temporarily removed only the locally generated package's
  `ffprobe.exe`; verification failed with `Required bundled executable not
  found`, and the binary and caller's `PATH` were restored afterward.
- The installer build now runs these checks before Inno Setup and stops on
  native build-command failures. Windows CI discovers the full test suite and
  uploads package-verification JSON reports. These workflow changes have not
  yet been run on GitHub Actions.
- WIN-405 remains `IN_REVIEW`: manual child-console, interactive GUI render,
  and separate live-system checks have not been completed. At this earlier
  stage Inno Setup was not installed locally; the subsequent source-build and
  local installer checks are recorded below.

### Source-Built Bundle and Local Installer Evidence (2026-10-17)

- Built FFmpeg 9.0.1, x264, and zlib 1.3.2 from the pinned commits with the
  isolated MSYS2 UCRT64 toolchain (GCC 16.2.0). Both executables passed the x64
  PE/system-DLL audit. They identify themselves as `9.0.1-trivia-countdown`;
  exported source snapshots are fenced off from the parent application's Git
  repository so upstream version scripts cannot inherit the app's version tag.
- All 34 discovered tests passed with the source-built tools, including UNC
  and long-path renders (no skips). The dedicated WIN-302 verifier also passed
  all required individual cases with long paths enabled. Report:
  `build/verification/WIN-302-20261017-175440.log`.
- Built `dist/Trivia-Countdown-0.1.0-Windows-x64-Setup.exe` with Inno Setup
  7.1.0 after the frozen preview, audio/silent render, and decode checks passed.
  Report:
  `build/verification/WIN-405-20261017-175454-b00277de67da47d1bf2701ee2c50a716.json`.
- Installer SHA-256:
  `a17ecc717d0f713faeb97a07020769e8751e134d41670ce4a11900c53df5715d`.
  The source archive SHA-256 is
  `b2f79c0efd8f29d439556b36fbdaec6452cf5694acbdb3a19c7d6d87fb1b0cfb`.
  Both match `dist/Trivia-Countdown-0.1.0-Windows-x64-SHA256SUMS.txt`.
- Compared every archived source file with a fresh `git archive` of its pinned
  commit (Git CRLF conversion disabled): 10,422 FFmpeg files, 270 x264 files,
  and 262 zlib files matched, with no missing or extra source files. The actual
  compile script, rebuild README, configuration reports, toolchain inventory,
  and required license/exception files were present. Report:
  `build/verification/Windows-source-archive-review-20261017.json`.
- Installed the candidate into an isolated local path containing Unicode,
  spaces, and an apostrophe, after guarding against an existing installation.
  Installed preview/render checks passed without system Python/FFmpeg on
  `PATH`; repeated after a same-version reinstall. Reports:
  `build/verification/WIN-405-20261017-175714-8218ad90db8d4bf9b168a302e51c88c1.json`
  and `build/verification/WIN-405-20261017-175723-098cd533be3c487aaa3bbff79be4c2f5.json`.
  Uninstall removed the test installation and its registration. No existing
  installation was overwritten and no test application was left installed.
- This was local automation on the development Windows 11 system, with icons
  suppressed. It is not separate live-system qualification, a version-changing
  upgrade test, visual icon/DPI approval, or human playback inspection. WIN-405,
  WIN-501, and WIN-504 remain `IN_REVIEW`. The updated source/archive provenance
  workflow has not yet run on GitHub Actions; WIN-502/WIN-503 remain `IN_REVIEW`.
- Run source environment sync/checks and package builds sequentially: an exact
  source-only `uv sync --frozen` prunes build dependencies and can conflict with
  a running PyInstaller process. The initial parallel verification attempt hit
  that environment conflict; the recorded successful verifier/build ran in
  sequence after restoring the locked build environment.

### BLK-001 Corresponding-Source Investigation and Replacement

- 2026-10-17, before the source-build decision: confirmed the supplier release links FFmpeg commit
  `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa` but does not attach the complete
  static dependency sources and build scripts. That former supplier executable
  uses `--enable-version3` and its supplied license is GPLv3.
- The supplier requested official-email contact in an existing source-manifest
  issue for another version. No request has been sent on the maintainer's
  behalf. The approved replacement avoids needing that supplier's materials:
  pinned FFmpeg 9.0.1, x264, and zlib 1.3.2 are built directly with external
  autodetection disabled, and both executables are installed with the GUI.
- The build generated
  `dist/Trivia-Countdown-FFmpeg-9.0.1-Windows-x64-sources.tar.gz` with clean
  source trees, exact revisions/URLs, the actual compile script, configurations,
  DLL-import reports, toolchain versions, and FFmpeg/x264/zlib/runtime notices.
  It does not reuse the former Gyan or macOS source archives. See
  [the source and rebuild guide](../packaging/FFMPEG_WINDOWS_SOURCE_README.md).
- BLK-001 is resolved by source availability. WIN-402, WIN-503, and WIN-603 are
  `IN_REVIEW`, not verified: source/license review, installed-file inspection,
  release attachment, and GitHub provenance remain outstanding. Nothing has
  been published.

### Final Automation and Qualification Handoff (2026-10-17)

- All 42 discovered tests passed locally with the source-built FFmpeg bundle,
  including UNC and long paths, without skips. Compilation and CLI help passed.
  New tests cover missing Tkinter, actionable CLI filesystem/process errors,
  cancellation at FFmpeg exit, a real GUI-generated PowerShell command, actual
  FFmpeg cancellation/cleanup, Windows locked-handle overwrite safety, and
  offline execution of both workflows' draft-release safety guards.
- Fixed the source GUI command to include PowerShell's `&` call operator before
  its quoted executable. Added a final cancellation check before output
  replacement, preserving an existing output when cancellation arrives as
  FFmpeg exits.
- Repeated the dedicated path verifier, then checked that all five caller
  environment variables were restored. Report:
  `build/verification/WIN-302-20261017-223713.log`.
- The installer now enforces Windows 10 22H2/native x64, embeds the application
  icon, and installs a sample CSV. A fresh local Inno Setup build and frozen
  preview/audio/silent/decode checks passed after these changes.
- Installed that rebuilt candidate into a guarded, isolated local path with
  spaces, Unicode, and an apostrophe. Verified the sample CSV and installed
  runtime/font/media/compiler-license resources, reran the frozen render checks,
  and uninstalled it. Application and registration removal passed. Reports:
  `build/verification/WIN-501-local-20261017-224316.json` and
  `build/verification/WIN-405-20261017-224324-c88a77c701e549d09df74d33cf3123f7.json`.
  This does not approve separate-system, visual, DPI, playback, or upgrade checks.
- A fresh local clone of `bce7b8b298d9ce870dd922b820b23cf9eee5f73e` passed
  documented source setup, Tcl/Tk 8.6, compile, all 40 then-current tests with
  configured UNC/long-path roots, GUI startup, and CLI help. Shell scripts kept
  LF line endings; the clone's working tree remained clean and the temporary
  checkout was removed. Report:
  `build/verification/Windows-fresh-source-20261017-224449.json`.
- Added draft-only Windows prerelease automation, serialized with macOS draft
  updates, with published-release replacement forbidden. Branch runs intentionally
  produce artifacts only. Workflow syntax passed actionlint 1.7.12.
- [Windows source run 39094563703](https://github.com/princeendo/trivia_countdown/actions/runs/39094563703)
  passed at `bce7b8b298d9ce870dd922b820b23cf9eee5f73e`: 40 tests ran, with six
  media-dependent cases skipped because system FFmpeg is absent in that job.
  The package job reruns the suite with the source-built tools. The initial
  CI attempt exposed PowerShell 7's inherited module path in Windows PowerShell
  5.1 test children; the tests now let each child initialize its own module path.
- The latest macOS regression build passed; its downloaded checksums and
  workflow/commit/ref provenance checks passed as recorded under WIN-305.
  Windows package CI is pending. Its source-pinned FFmpeg CI/provenance gates
  remain open until the new artifacts are built, downloaded, and verified.
- Separate-system human approval cannot proceed: the user confirmed that a
  second live Windows system is unavailable. BLK-007 records this blocker.
  [The qualification checklist](windows_preview_qualification.md) covers all
  remaining manual, source/license, DPI, playback, and upgrade approvals.
  No new release or version tag has been created; published `v0.1.0` is unchanged.

## Phase 6: Documentation

| ID | Task | Priority | Status | Blocker | Dependencies | Acceptance Criteria | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WIN-601 | Update the README and user documentation | `P0` | `IN_REVIEW` | None | Finalized setup, packaging, and release behavior | `README.md` and every file under `docs/` accurately cover Windows installation, PowerShell usage, paths, SmartScreen, troubleshooting, supported systems, privacy, and release procedures without making macOS instructions ambiguous. | Follow all Windows instructions from a clean system; check every link and duplicated command. |
| WIN-602 | Update maintainer guidance | `P1` | `IN_REVIEW` | None | WIN-203, WIN-502 | `AGENTS.md` contains platform-neutral setup and verification commands and the Windows package/release checks. | Execute documented commands in PowerShell and macOS CI. |
| WIN-603 | Update third-party and source notices | `P0` | `IN_REVIEW` | None | WIN-402 | `THIRD_PARTY_NOTICES.md` and packaging documentation describe both macOS and Windows artifacts, native Pillow libraries, bundled fonts, FFmpeg provenance, and corresponding source locations. | License review and artifact inspection. |

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
| `READY` tasks | 0 |
| `IN_PROGRESS` tasks | 0 |
| `IN_REVIEW` tasks | 12 |
| `BLOCKED` tasks | 3 |
| `DEFERRED` tasks | 1 |
| `VERIFIED` implementation tasks | 16 |

Update this summary whenever task statuses change. Do not mark implementation
tasks `VERIFIED` until their listed Windows verification has passed.
