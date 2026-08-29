"""Progress and duration formatting helpers."""

from __future__ import annotations

import os
import sys
import time


def format_seconds(value: float) -> str:
    return f"{value:g}s"


def format_duration(seconds: float) -> str:
    seconds = max(0.0, seconds)
    if seconds < 60:
        return f"{seconds:.1f}s"

    total_seconds = round(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, remaining_seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {remaining_seconds:02d}s"
    return f"{minutes}m {remaining_seconds:02d}s"


class ProgressReporter:
    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled

    def update_units(self, phase: str, completed: int, total: int, phase_start: float) -> None:
        if total <= 0:
            return
        fraction = min(1.0, max(0.0, completed / total))
        detail = f"{completed}/{total}"
        self.update_fraction(phase, fraction, detail, phase_start)

    def update_fraction(self, phase: str, fraction: float, detail: str, phase_start: float) -> None:
        if not self.enabled:
            return

        fraction = min(1.0, max(0.0, fraction))
        elapsed = time.monotonic() - phase_start
        if fraction > 0:
            remaining = elapsed * (1 - fraction) / fraction
            remaining_text = format_duration(remaining)
        else:
            remaining_text = "calculating"

        message = (
            f"{phase}: {fraction * 100:5.1f}% ({detail}) "
            f"elapsed {format_duration(elapsed)}, remaining {remaining_text}"
        )
        if self._is_interactive():
            suffix = "\033[K" if self._supports_ansi() else ""
            print(f"\r{message}{suffix}", end="", file=sys.stderr, flush=True)
        else:
            print(message, file=sys.stderr, flush=True)

    def complete_phase(self, phase: str, phase_start: float) -> None:
        if not self.enabled:
            return
        elapsed = time.monotonic() - phase_start
        suffix = "\033[K" if self._supports_ansi() else ""
        prefix = "\r" if self._is_interactive() else ""
        print(f"{prefix}{phase}: complete in {format_duration(elapsed)}{suffix}", file=sys.stderr, flush=True)

    @staticmethod
    def _is_interactive() -> bool:
        return bool(getattr(sys.stderr, "isatty", lambda: False)())

    @staticmethod
    def _supports_ansi() -> bool:
        if not ProgressReporter._is_interactive():
            return False
        if os.name != "nt":
            return True
        return bool(os.environ.get("ANSICON") or os.environ.get("WT_SESSION") or os.environ.get("ConEmuANSI") == "ON")
