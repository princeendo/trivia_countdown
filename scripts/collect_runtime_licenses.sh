#!/bin/bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
DESTINATION="$ROOT/build/vendor/licenses"

uv sync --group build --frozen

PYTHON_LICENSE=$(uv run python -c 'from pathlib import Path; import sys; print(Path(sys.base_prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "LICENSE.txt")')
PILLOW_LICENSE=$(uv run python -c 'import importlib.metadata as metadata; print(metadata.distribution("Pillow")._path / "licenses" / "LICENSE")')
PYINSTALLER_LICENSE=$(uv run python -c 'import importlib.metadata as metadata; print(metadata.distribution("pyinstaller")._path / "licenses" / "COPYING.txt")')

for license_file in "$PYTHON_LICENSE" "$PILLOW_LICENSE" "$PYINSTALLER_LICENSE"; do
    if [[ ! -f "$license_file" ]]; then
        echo "error: runtime license not found: $license_file" >&2
        exit 1
    fi
done

mkdir -p "$DESTINATION"
rm -f \
    "$DESTINATION/PYTHON-LICENSE.txt" \
    "$DESTINATION/PILLOW-AND-NATIVE-LIBRARIES-LICENSE.txt" \
    "$DESTINATION/PYINSTALLER-LICENSE.txt" \
    "$DESTINATION/TCL-LICENSE.txt" \
    "$DESTINATION/TK-LICENSE.txt" \
    "$DESTINATION/TCL-TK-LICENSE.txt"
install -m 644 "$PYTHON_LICENSE" "$DESTINATION/PYTHON-LICENSE.txt"
install -m 644 "$PILLOW_LICENSE" "$DESTINATION/PILLOW-AND-NATIVE-LIBRARIES-LICENSE.txt"
install -m 644 "$PYINSTALLER_LICENSE" "$DESTINATION/PYINSTALLER-LICENSE.txt"
install -m 644 "$ROOT/packaging/licenses/TCL-LICENSE.txt" "$DESTINATION/TCL-LICENSE.txt"
install -m 644 "$ROOT/packaging/licenses/TK-LICENSE.txt" "$DESTINATION/TK-LICENSE.txt"
