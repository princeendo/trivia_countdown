#!/bin/bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
VERSION=$(uv run --frozen python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
APP="$ROOT/dist/Trivia Countdown.app"
DMG="$ROOT/dist/Trivia-Countdown-$VERSION-macOS-arm64.dmg"
STAGING="$ROOT/build/dmg"

if [[ $(uname -s) != "Darwin" || $(uname -m) != "arm64" ]]; then
    echo "error: the prototype app build requires an Apple Silicon Mac" >&2
    exit 1
fi
if [[ ! -x "$ROOT/build/vendor/bin/ffmpeg" || ! -x "$ROOT/build/vendor/bin/ffprobe" ]]; then
    echo "error: run scripts/build_ffmpeg_macos.sh first" >&2
    exit 1
fi

"$ROOT/scripts/create_macos_icon.sh"
uv sync --group build --frozen
"$ROOT/scripts/collect_runtime_licenses.sh"
uv run pyinstaller --noconfirm --clean "$ROOT/packaging/TriviaCountdown.spec"

codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

rm -rf "$STAGING"
mkdir -p "$STAGING"
cp -R "$APP" "$STAGING/Trivia Countdown.app"
ln -s /Applications "$STAGING/Applications"
cp "$ROOT/LICENSE" "$STAGING/LICENSE.txt"
cp "$ROOT/THIRD_PARTY_NOTICES.md" "$STAGING/THIRD_PARTY_NOTICES.md"
cp -R "$ROOT/build/vendor/licenses" "$STAGING/Third-Party Licenses"
cp "$ROOT/sample_objects/sample_of_5_trivia_questions.csv" "$STAGING/Sample Trivia Questions.csv"

rm -f "$DMG" "$ROOT/dist/SHA256SUMS"
hdiutil create \
    -volname "Trivia Countdown" \
    -srcfolder "$STAGING" \
    -format UDZO \
    -ov \
    "$DMG"
hdiutil verify "$DMG"
(
    cd "$ROOT/dist"
    shasum -a 256 "$(basename "$DMG")" Trivia-Countdown-FFmpeg-*-sources.tar.gz > SHA256SUMS
)

echo "Built $DMG"
