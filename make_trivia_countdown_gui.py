#!/usr/bin/env python3
"""Launch the Trivia Countdown desktop interface."""

import sys

try:
    from trivia_countdown.gui import main
except ImportError as exc:
    if exc.name in {"tkinter", "_tkinter"}:
        print("error: Tkinter is unavailable in this Python installation.", file=sys.stderr)
        print("Install a Python build with Tcl/Tk support, then run this command again.", file=sys.stderr)
        raise SystemExit(1) from exc
    raise


if __name__ == "__main__":
    raise SystemExit(main())
