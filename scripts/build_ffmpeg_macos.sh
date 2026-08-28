#!/bin/bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
BUILD_ROOT="$ROOT/build/ffmpeg"
SOURCE_ROOT="$BUILD_ROOT/sources"
PREFIX="$BUILD_ROOT/prefix"
VENDOR_BIN="$ROOT/build/vendor/bin"
VENDOR_LICENSES="$ROOT/build/vendor/licenses"
DIST="$ROOT/dist"
FFMPEG_VERSION="n8.0.1"
FFMPEG_COMMIT="d22ecc4f6f3fca77b3e71b18641ceddb25973e97"
X264_COMMIT="b35605ace3ddf7c1a5d67a2eb553f034aef41d55"

for command in git tar; do
    command -v "$command" >/dev/null || {
        echo "error: required build command not found: $command" >&2
        exit 1
    }
done

mkdir -p "$SOURCE_ROOT" "$PREFIX" "$VENDOR_BIN" "$VENDOR_LICENSES" "$DIST"

checkout_source() {
    local url=$1
    local destination=$2
    local commit=$3
    if [[ ! -d "$destination/.git" ]]; then
        git clone --filter=blob:none "$url" "$destination"
    fi
    git -C "$destination" fetch --depth=1 origin "$commit"
    git -C "$destination" checkout --detach "$commit"
}

checkout_source "https://code.videolan.org/videolan/x264.git" "$SOURCE_ROOT/x264" "$X264_COMMIT"
checkout_source "https://git.ffmpeg.org/ffmpeg.git" "$SOURCE_ROOT/ffmpeg" "$FFMPEG_COMMIT"

"$ROOT/scripts/compile_ffmpeg_macos.sh" "$SOURCE_ROOT/x264" "$SOURCE_ROOT/ffmpeg" "$PREFIX" "$VENDOR_BIN"
install -m 644 "$SOURCE_ROOT/ffmpeg/COPYING.GPLv2" "$VENDOR_LICENSES/GPL-2.0.txt"

SOURCE_PACKAGE="$DIST/Trivia-Countdown-FFmpeg-$FFMPEG_VERSION-sources.tar.gz"
PACKAGE_ROOT="$BUILD_ROOT/source-package"
rm -f "$DIST"/Trivia-Countdown-FFmpeg-*-sources.tar.gz
rm -rf "$PACKAGE_ROOT"
mkdir -p "$PACKAGE_ROOT/ffmpeg-$FFMPEG_VERSION" "$PACKAGE_ROOT/x264-$X264_COMMIT"
git -C "$SOURCE_ROOT/ffmpeg" archive "$FFMPEG_COMMIT" | tar -x -C "$PACKAGE_ROOT/ffmpeg-$FFMPEG_VERSION"
git -C "$SOURCE_ROOT/x264" archive "$X264_COMMIT" | tar -x -C "$PACKAGE_ROOT/x264-$X264_COMMIT"
cp "$ROOT/scripts/compile_ffmpeg_macos.sh" "$PACKAGE_ROOT/BUILD-FFMPEG.sh"
chmod +x "$PACKAGE_ROOT/BUILD-FFMPEG.sh"
cp "$ROOT/packaging/FFMPEG_SOURCE_README.md" "$PACKAGE_ROOT/README.md"
cp "$SOURCE_ROOT/ffmpeg/COPYING.GPLv2" "$PACKAGE_ROOT/GPL-2.0.txt"
tar -czf "$SOURCE_PACKAGE" -C "$PACKAGE_ROOT" .

echo "Built bundled FFmpeg tools and $SOURCE_PACKAGE"
