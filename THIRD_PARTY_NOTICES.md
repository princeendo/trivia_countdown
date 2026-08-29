# Third-Party Notices

Trivia Countdown includes Python, Tcl/Tk, Pillow, Pillow's native libraries,
the PyInstaller bootloader, and FFmpeg executables built with x264 support.
Their full license texts are included in the **Third-Party Licenses** folder in
the DMG and in the app.

## Python, Tcl/Tk, and Pillow

- Python: https://www.python.org/
- Tcl/Tk: https://www.tcl.tk/
- Pillow: https://python-pillow.github.io/
- PyInstaller: https://pyinstaller.org/

Pillow's distributed license file also contains the notices for native image
libraries shipped in its macOS wheel.

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
