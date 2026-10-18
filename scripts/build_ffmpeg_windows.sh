#!/bin/bash
set -euo pipefail
[[ ${MSYSTEM:-} == UCRT64 ]] || { echo 'error: use MSYS2 UCRT64' >&2; exit 1; }
ROOT=$(cd "$(dirname "$0")/.." && pwd)
if [[ "$ROOT" == *' '* || "$ROOT" == *"'"* ]]; then
    echo 'error: build FFmpeg from a checkout path without spaces or apostrophes' >&2
    exit 1
fi
BUILD="$ROOT/build/ffmpeg-windows"
VENDOR="$ROOT/build/vendor/windows"
FFMPEG_COMMIT=bf1b838f2ab88b4f8fd83443325c782ea0e0f7fa
X264_COMMIT=b35605ace3ddf7c1a5d67a2eb553f034aef41d55
ZLIB_COMMIT=da607da739fa6047df13e66a2af6b8bec7c2a498
export PATH=/ucrt64/bin:/usr/bin
mkdir -p "$BUILD/cache" "$ROOT/dist"
STAGING=$(mktemp -d "$BUILD/build.XXXXXX")
trap 'rm -rf -- "$STAGING"' EXIT
SOURCES="$STAGING/source-package"
mkdir -p "$SOURCES" "$STAGING/bin"

archive_source() {
    local name=$1 url=$2 commit=$3
    local cache="$BUILD/cache/$name.git"
    [[ -d "$cache" ]] || git init --bare "$cache"
    git -C "$cache" fetch --depth=1 "$url" "$commit"
    [[ $(git -C "$cache" rev-parse FETCH_HEAD) == "$commit" ]]
    mkdir -p "$SOURCES/$name"
    git -C "$cache" archive "$commit" | tar -x -C "$SOURCES/$name"
    printf '%s %s %s\n' "$name" "$commit" "$url" >> "$SOURCES/SOURCES.txt"
}
archive_source ffmpeg https://github.com/FFmpeg/FFmpeg.git "$FFMPEG_COMMIT"
archive_source x264 https://code.videolan.org/videolan/x264.git "$X264_COMMIT"
archive_source zlib https://github.com/madler/zlib.git "$ZLIB_COMMIT"
cp "$ROOT/scripts/compile_ffmpeg_windows.sh" "$SOURCES/BUILD-FFMPEG.sh"
cp "$ROOT/packaging/FFMPEG_WINDOWS_SOURCE_README.md" "$SOURCES/README.md"
pacman -Q > "$SOURCES/BUILD-PACKAGES.txt"
gcc --version > "$SOURCES/COMPILER.txt"
mkdir -p "$SOURCES/configuration" "$SOURCES/licenses"
cp "$SOURCES/ffmpeg/COPYING.GPLv2" "$SOURCES/licenses/FFMPEG-GPL-2.0.txt"
cp "$SOURCES/x264/COPYING" "$SOURCES/licenses/X264-GPL-2.0.txt"
cp "$SOURCES/zlib/LICENSE" "$SOURCES/licenses/ZLIB-LICENSE.txt"
cp "$ROOT/LICENSE" "$SOURCES/licenses/BUILD-SCRIPTS-MIT.txt"
cp -a /ucrt64/share/licenses/libgcc "$SOURCES/licenses/GCC-runtime"
cp -a /ucrt64/share/licenses/crt "$SOURCES/licenses/MinGW-runtime"
cp -a /ucrt64/share/licenses/headers "$SOURCES/licenses/MinGW-headers"
bash "$SOURCES/BUILD-FFMPEG.sh" "$SOURCES/x264" "$SOURCES/ffmpeg" "$SOURCES/zlib" "$STAGING/work" "$STAGING/bin" 2>&1 | tee "$BUILD/compile.log"
cp "$STAGING/work/ffmpeg/config.h" "$STAGING/work/ffmpeg/ffbuild/config.mak" "$SOURCES/configuration/"
cp "$STAGING/work/x264/config.h" "$SOURCES/configuration/x264-config.h"
cp "$STAGING/bin/"*-version.txt "$STAGING/bin/"*-pe.txt "$SOURCES/configuration/"
PACKAGE="Trivia-Countdown-FFmpeg-9.0.1-Windows-x64-sources.tar.gz"
tar -czf "$STAGING/$PACKAGE" -C "$SOURCES" .

# Replace only the named generated files after successful compilation/auditing.
mkdir -p "$VENDOR/bin" "$VENDOR/licenses"
cp "$STAGING/bin/ffmpeg.exe" "$STAGING/bin/ffprobe.exe" "$VENDOR/bin/"
cp -a "$SOURCES/licenses/." "$VENDOR/licenses/"
cp "$SOURCES/ffmpeg/COPYING.GPLv2" "$VENDOR/LICENSE"
cp "$SOURCES/SOURCES.txt" "$VENDOR/SOURCES.txt"
cp "$STAGING/$PACKAGE" "$ROOT/dist/$PACKAGE"
(cd "$VENDOR" && sha256sum bin/ffmpeg.exe bin/ffprobe.exe) > "$VENDOR/SHA256SUMS"
echo "Built self-contained Windows FFmpeg and $PACKAGE"
