#!/bin/bash
set -euo pipefail

if [[ $# -ne 5 || ${MSYSTEM:-} != UCRT64 ]]; then
    echo 'usage (MSYS2 UCRT64): compile_ffmpeg_windows.sh X264_SOURCE FFMPEG_SOURCE ZLIB_SOURCE WORK_DIRECTORY OUTPUT_DIRECTORY' >&2
    exit 1
fi
X264_SOURCE=$(cd "$1" && pwd)
FFMPEG_SOURCE=$(cd "$2" && pwd)
ZLIB_SOURCE=$(cd "$3" && pwd)
mkdir -p "$4" "$5"
WORK=$(cd "$4" && pwd)
OUTPUT=$(cd "$5" && pwd)
# Exported source snapshots live inside the application's checkout during a
# maintainer build. Never let upstream version scripts discover its Git tags.
export GIT_CEILING_DIRECTORIES="$(dirname "$X264_SOURCE"):$(dirname "$FFMPEG_SOURCE"):$WORK"
if [[ "$WORK" == *' '* || "$WORK" == *"'"* ]]; then
    echo 'error: compiler work directory must not contain spaces or apostrophes' >&2
    exit 1
fi
export PATH=/ucrt64/bin:/usr/bin
for command in gcc make nasm pkg-config objdump; do command -v "$command" >/dev/null; done
[[ $(gcc -dumpmachine) == x86_64-w64-mingw32 ]]
PREFIX="$WORK/prefix"
mkdir -p "$PREFIX/include" "$PREFIX/lib/pkgconfig" "$WORK/zlib" "$WORK/x264" "$WORK/ffmpeg"
export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig"
unset PKG_CONFIG_PATH
JOBS=${NUMBER_OF_PROCESSORS:-4}

# zlib is required for PNG overlays and previews. Build it, rather than linking
# the toolchain's prebuilt copy and losing track of its corresponding source.
cp -a "$ZLIB_SOURCE/." "$WORK/zlib/"
pushd "$WORK/zlib" >/dev/null
make -f win32/Makefile.gcc -j"$JOBS" libz.a
cp libz.a "$PREFIX/lib/"
cp zlib.h zconf.h "$PREFIX/include/"
cat > "$PREFIX/lib/pkgconfig/zlib.pc" <<EOF
prefix=$PREFIX
libdir=\${prefix}/lib
includedir=\${prefix}/include
Name: zlib
Description: zlib compression library
Version: 1.3.2
Libs: -L\${libdir} -lz
Cflags: -I\${includedir}
EOF
popd >/dev/null

pushd "$WORK/x264" >/dev/null
"$X264_SOURCE/configure" --prefix="$PREFIX" --host=x86_64-w64-mingw32 \
    --enable-static --disable-cli --disable-opencl --disable-avs --disable-lavf --disable-swscale
make -j"$JOBS"
make install-lib-static
popd >/dev/null

pushd "$WORK/ffmpeg" >/dev/null
"$FFMPEG_SOURCE/configure" \
    --prefix="$PREFIX" --arch=x86_64 --target-os=mingw32 --cc=gcc \
    --extra-cflags="-I$PREFIX/include" \
    --extra-ldflags="-L$PREFIX/lib -static -static-libgcc" \
    --pkg-config-flags=--static --disable-autodetect \
    --enable-gpl --enable-libx264 --enable-zlib \
    --enable-static --disable-shared --disable-pthreads --enable-w32threads \
    --disable-debug --disable-doc --disable-ffplay --extra-version=trivia-countdown
make -j"$JOBS"
cp ffmpeg.exe ffprobe.exe "$OUTPUT/"
popd >/dev/null

# Reject non-system DLLs, including MSYS2, libgcc, and winpthread runtimes.
for binary in ffmpeg ffprobe; do
    objdump -f "$OUTPUT/$binary.exe" | grep -q 'pei-x86-64'
    objdump -p "$OUTPUT/$binary.exe" > "$OUTPUT/$binary-pe.txt"
    while read -r dll; do
        case "${dll,,}" in
            kernel32.dll|msvcrt.dll|ucrtbase.dll|advapi32.dll|avicap32.dll|avrt.dll|bcrypt.dll|crypt32.dll|gdi32.dll|ntdll.dll|ole32.dll|oleaut32.dll|psapi.dll|secur32.dll|shell32.dll|shlwapi.dll|user32.dll|vfw32.dll|winmm.dll|ws2_32.dll|api-ms-win-*.dll) ;;
            *) echo "error: unexpected runtime dependency in $binary: $dll" >&2; exit 1 ;;
        esac
    done < <(awk '/DLL Name:/ {print $3}' "$OUTPUT/$binary-pe.txt")
    "$OUTPUT/$binary.exe" -hide_banner -version > "$OUTPUT/$binary-version.txt"
done
