# Trivia Countdown Windows FFmpeg Sources

The Windows installer bundles native x64 `ffmpeg.exe` and `ffprobe.exe`; users
do not install FFmpeg, MSYS2, Python, or a compiler separately. The executables
are separate subprocesses, not libraries linked into the MIT-licensed Python
application.

## Source and License Scope

Our Windows build uses only these third-party media/compression libraries:

| Component | Exact revision | License |
| --- | --- | --- |
| FFmpeg 9.0.1 | `bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa` | GPLv2 or later with this configuration |
| x264 | `b35605ace3ddf7c1a5d67a2eb553f034aef41d55` | GPLv2 or later |
| zlib 1.3.2 | `da607da739fa6047df13e66a2af6b8bec7c2a498` | zlib license |

External-library autodetection is disabled. x264 provides H.264 encoding,
FFmpeg provides its native AAC encoder, and zlib supports PNG overlays and
previews. FFmpeg's built-in decoders and demuxers remain enabled. Optional
external codecs such as libaom/libdav1d AV1 decoding, proprietary plugins, GPU
acceleration libraries, and subtitle-rendering libraries are not bundled.
This is not the old Gyan Essentials build. In particular, we do not enable
`--enable-version3`, x265, or other external GPLv3 dependencies.

The matching `Trivia-Countdown-FFmpeg-9.0.1-Windows-x64-sources.tar.gz` contains
the exact source trees, `SOURCES.txt` revision/URL manifest, build script,
configuration records, toolchain package list, and applicable FFmpeg, x264,
zlib, MinGW-w64, and GCC runtime license/exception texts. The compiler and its
MSYS2 build tools are build-time dependencies, not installed with the app.
The native executable audit rejects non-system DLL dependencies.

## Rebuilding From a Source Archive

Use a Windows x64 build machine with MSYS2's UCRT64 environment and these
packages (the actual build's versions are in `BUILD-PACKAGES.txt`):

```sh
pacman -S --needed make diffutils mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-nasm mingw-w64-ucrt-x86_64-pkgconf
```

Extract the archive to a directory without spaces or apostrophes, open an
MSYS2 **UCRT64** shell there, then run:

```sh
bash BUILD-FFMPEG.sh "$PWD/x264" "$PWD/ffmpeg" "$PWD/zlib" "$PWD/rebuild" "$PWD/bin"
```

The output directory will contain both executables, version/configuration
reports, and PE dependency reports. Windows system APIs and the Universal C
Runtime are required. Sources are pinned; toolchain updates and filesystem
metadata can change the resulting binary hashes. Byte-for-byte reproducibility
is not promised.

## Building From This Repository

From Windows PowerShell in the checkout:

```powershell
.\scripts\setup_windows_ffmpeg_tools.ps1
.\scripts\build_ffmpeg_windows.ps1
```

The setup helper downloads a hash-pinned MSYS2 base into `build\tools\msys64`
and installs/updates its build tools without changing the system `PATH` or
creating Start Menu entries. The build fetches pinned Git commits into
`build\ffmpeg-windows\cache`, compiles clean source snapshots in a temporary
build tree, and writes binaries/notices under `build\vendor\windows` and the
matching source archive under `dist`. Intermediate build trees are removed;
the Git cache remains for future builds. A custom existing MSYS2 installation
can be selected with `build_ffmpeg_windows.ps1 -Msys2Root 'C:\msys64'`.

Every Windows release must publish the matching source archive with the
installer, SHA-256 checksums, and build provenance. A successful local build
does not replace license review or live installer qualification.
