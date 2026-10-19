# Third-Party Notices

Trivia Countdown includes Python, Tcl/Tk, Pillow, Pillow's native libraries,
the PyInstaller bootloader, Noto Sans fonts, and FFmpeg executables built with
x264 support. Their license texts are included in the **Third-Party Licenses**
folder on the macOS DMG and under `_internal/licenses/` in the Windows
installation directory.

## Python, Tcl/Tk, and Pillow

- Python: https://www.python.org/
- Tcl/Tk: https://www.tcl.tk/
- Pillow: https://python-pillow.github.io/
- PyInstaller: https://pyinstaller.org/

Pillow's distributed license file also contains the notices for native image
libraries shipped in its platform-specific wheel.

## Noto Sans

The application bundles Noto Sans Regular and Bold from the Noto Fonts
`v20201206-phase3` revision `20bc5918912503bc1537a407a694738c33c048aa`.
The fonts are distributed under the SIL Open Font License 1.1. The exact font
hashes and license text are in [`assets/fonts/`](assets/fonts/).

- Noto Fonts: https://github.com/notofonts/noto-fonts
- SIL Open Font License 1.1: https://openfontlicense.org/

## FFmpeg and x264

The bundled FFmpeg executables are built with x264 support and distributed
under the GNU General Public License, version 2 or later. Windows builds are
compiled from pinned FFmpeg 9.0.1, x264, and zlib sources with external-library
autodetection disabled. They do not use the former Gyan Essentials binary
bundle. Copyright belongs to the respective FFmpeg and library contributors.

- FFmpeg: https://ffmpeg.org/
- x264: https://www.videolan.org/developers/x264.html
- zlib: https://zlib.net/
- GPL version 2: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

The exact corresponding sources, including the build script used for this
application, must be published beside each DMG or Windows installer on the project's GitHub
Releases page: https://github.com/princeendo/trivia_countdown/releases

Microsoft Store MSIX candidates use the same Windows media build and include
these notices and license texts under `app/_internal/` in the package. The
package's `StoreBuild.json` records the app/Store versions and corresponding
Windows source archive filename and SHA-256. Before a Store version is
distributed, provide its exact source archive and rebuild instructions at a
durable public URL in the listing/support materials. Retain those materials
after later updates; private CI artifacts are not public source distribution.

Windows source archives contain FFmpeg, x264, zlib, and their build materials.
Windows applications also include zlib, MinGW-w64 runtime notices, and GCC
runtime license/exception texts in their third-party licenses directory. See
the [Windows source and rebuild guide](https://github.com/princeendo/trivia_countdown/blob/master/packaging/FFMPEG_WINDOWS_SOURCE_README.md).
Do not substitute a macOS source archive for the Windows archive.

Run `ffmpeg -version` from the bundled executable to see its complete build
configuration and library versions.
