"""Cancellation primitives shared by rendering and user interfaces."""

from __future__ import annotations

from threading import Event
from typing import Callable, Optional


class RenderCancelled(RuntimeError):
    """Raised when a caller cancels an in-progress render."""


class CancellationToken:
    """Thread-safe cancellation state for a single render job."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    def cancelled(self) -> bool:
        return self._event.is_set()


def check_cancelled(cancel_check: Optional[Callable[[], bool]]) -> None:
    if cancel_check and cancel_check():
        raise RenderCancelled("Render cancelled")
