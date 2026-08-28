#!/bin/bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
SOURCE="$ROOT/assets/app_icon.png"
OUTPUT_DIR="$ROOT/build/macos"
ICONSET="$OUTPUT_DIR/TriviaCountdown.iconset"

rm -rf "$ICONSET"
mkdir -p "$ICONSET"

while read -r filename size; do
    sips -z "$size" "$size" "$SOURCE" --out "$ICONSET/$filename" >/dev/null
done <<'EOF'
icon_16x16.png 16
icon_16x16@2x.png 32
icon_32x32.png 32
icon_32x32@2x.png 64
icon_128x128.png 128
icon_128x128@2x.png 256
icon_256x256.png 256
icon_256x256@2x.png 512
icon_512x512.png 512
icon_512x512@2x.png 1024
EOF

iconutil -c icns "$ICONSET" -o "$OUTPUT_DIR/TriviaCountdown.icns"
rm -rf "$ICONSET"
