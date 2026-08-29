# Third-Party Notices

Trivia Countdown includes Python, Tcl/Tk, Pillow, Pillow's native libraries,
the PyInstaller bootloader, Noto Sans fonts, and FFmpeg executables built with
x264 support. Their full license texts are included in the **Third-Party
Licenses** folder in released applications.

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

The bundled FFmpeg executables are built with x264 support and are distributed
under the GNU General Public License, version 2 or later. Copyright belongs to
the FFmpeg and x264 contributors.

- FFmpeg: https://ffmpeg.org/
- x264: https://www.videolan.org/developers/x264.html
- GPL version 2: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

The exact corresponding FFmpeg and x264 source code, including the build script
used for this application, is published beside each DMG on the project's GitHub
Releases page: https://github.com/princeendo/trivia_countdown/releases

Run `ffmpeg -version` from the bundled executable to see its complete build
configuration and library versions.
