"""Resolve application resources in source and frozen builds."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def windows_package_full_name() -> str | None:
    """Return the active MSIX identity, or None for an unpackaged process."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    get_name = ctypes.WinDLL("kernel32", use_last_error=True).GetCurrentPackageFullName
    get_name.argtypes = [ctypes.POINTER(wintypes.UINT), wintypes.LPWSTR]
    get_name.restype = wintypes.LONG
    length = wintypes.UINT()
    result = get_name(ctypes.byref(length), None)
    if result == 15700:  # APPMODEL_ERROR_NO_PACKAGE
        return None
    if result != 122:  # ERROR_INSUFFICIENT_BUFFER
        raise OSError(result, "Could not determine Windows package identity")
    buffer = ctypes.create_unicode_buffer(length.value)
    result = get_name(ctypes.byref(length), buffer)
    if result:
        raise OSError(result, "Could not read Windows package identity")
    return buffer.value


def resource_path(*parts: str) -> Path:
    if is_frozen():
        root = Path(getattr(sys, "_MEIPASS"))
    else:
        root = Path(__file__).resolve().parent.parent
    return root.joinpath(*parts)


def executable_path(name: str) -> Path:
    if is_frozen():
        bundled_name = name
        if sys.platform == "win32" and not name.lower().endswith(".exe"):
            bundled_name = f"{name}.exe"
        bundled = resource_path("bin", bundled_name)
        if bundled.is_file():
            return bundled
        raise RuntimeError(f"Required bundled executable not found: {bundled_name}")

    installed = shutil.which(name)
    if installed is None:
        raise RuntimeError(f"Required executable not found: {name}")
    return Path(installed)
