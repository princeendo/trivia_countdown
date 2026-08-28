#!/bin/bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
    echo "usage: $0 X264_SOURCE FFMPEG_SOURCE PREFIX OUTPUT_DIRECTORY" >&2
    exit 1
fi

X264_SOURCE=$(cd "$1" && pwd)
FFMPEG_SOURCE=$(cd "$2" && pwd)
PREFIX=$3
OUTPUT_DIRECTORY=$4

if [[ $(uname -s) != "Darwin" || $(uname -m) != "arm64" ]]; then
    echo "error: the prototype FFmpeg build requires an Apple Silicon Mac" >&2
    exit 1
fi

for command in make clang pkg-config; do
    command -v "$command" >/dev/null || {
        echo "error: required build command not found: $command" >&2
        exit 1
    }
done

mkdir -p "$PREFIX" "$OUTPUT_DIRECTORY"
PREFIX=$(cd "$PREFIX" && pwd)
OUTPUT_DIRECTORY=$(cd "$OUTPUT_DIRECTORY" && pwd)
export MACOSX_DEPLOYMENT_TARGET=14.0
export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig"

pushd "$X264_SOURCE" >/dev/null
make clean >/dev/null 2>&1 || true
./configure \
    --prefix="$PREFIX" \
    --host=aarch64-apple-darwin \
    --enable-static \
    --disable-cli \
    --disable-opencl
make -j"$(sysctl -n hw.logicalcpu)"
make install-lib-static
popd >/dev/null

pushd "$FFMPEG_SOURCE" >/dev/null
make distclean >/dev/null 2>&1 || true
./configure \
    --prefix="$PREFIX" \
    --arch=arm64 \
    --target-os=darwin \
    --cc=clang \
    --extra-cflags="-mmacosx-version-min=14.0 -I$PREFIX/include" \
    --extra-ldflags="-mmacosx-version-min=14.0 -L$PREFIX/lib" \
    --pkg-config-flags=--static \
    --disable-autodetect \
    --enable-gpl \
    --enable-libx264 \
    --enable-zlib \
    --enable-static \
    --disable-shared \
    --disable-debug \
    --disable-doc \
    --disable-ffplay
make -j"$(sysctl -n hw.logicalcpu)"
make install
popd >/dev/null

install -m 755 "$PREFIX/bin/ffmpeg" "$OUTPUT_DIRECTORY/ffmpeg"
install -m 755 "$PREFIX/bin/ffprobe" "$OUTPUT_DIRECTORY/ffprobe"

for binary in ffmpeg ffprobe; do
    file "$OUTPUT_DIRECTORY/$binary" | grep -q "arm64"
    if otool -L "$OUTPUT_DIRECTORY/$binary" | grep -qE '/opt/homebrew|/usr/local'; then
        echo "error: $binary contains a non-system runtime dependency" >&2
        exit 1
    fi
    codesign --force --sign - "$OUTPUT_DIRECTORY/$binary"
done
