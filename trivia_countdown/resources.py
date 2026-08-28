"""Resolve application resources in source and frozen builds."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_path(*parts: str) -> Path:
    if is_frozen():
        root = Path(getattr(sys, "_MEIPASS"))
    else:
        root = Path(__file__).resolve().parent.parent
    return root.joinpath(*parts)


def executable_path(name: str) -> Path:
    if is_frozen():
        bundled = resource_path("bin", name)
        if bundled.is_file():
            return bundled
        raise RuntimeError(f"Required bundled executable not found: {name}")

    installed = shutil.which(name)
    if installed is None:
        raise RuntimeError(f"Required executable not found: {name}")
    return Path(installed)
