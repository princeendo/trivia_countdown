# Building the Bundled FFmpeg Tools

This archive contains the exact FFmpeg and x264 source revisions distributed
with Trivia Countdown. On an Apple Silicon Mac with the Xcode Command Line
Tools and `pkg-config`, run `BUILD-FFMPEG.sh` with the included source folders:

```sh
mkdir -p build bin
./BUILD-FFMPEG.sh ./x264-* ./ffmpeg-* ./build ./bin
```

The resulting `bin/ffmpeg` and `bin/ffprobe` executables target macOS 14 or
later and use the same configure options as the distributed binaries.

## Windows Preview Status

The Windows packaging workflow currently pins Gyan FFmpeg 9.0.1 Essentials,
release asset `ffmpeg-9.0.1-essentials_build.zip`, SHA-256
`fec81ae03971d9dd4be3ebe02e263bd2ec1d789483f931bdba5f5715e65da2e9`.
The binary is static and GPLv3, with FFmpeg source revision `bf1b838f2a`.

Do not publish a Windows installer until the corresponding source archive for
FFmpeg, x264, and every other GPL-covered static component has been reviewed
and attached to the release. That archive is not yet produced by this project.
