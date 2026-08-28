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
