#!/usr/bin/env bash

if [ -n "${BASH_VERSION:-}" ]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
  if [[ "$SCRIPT_PATH" == "$0" ]]; then
    SOURCED=0
  else
    SOURCED=1
  fi
elif [ -n "${ZSH_VERSION:-}" ]; then
  SCRIPT_PATH="${(%):-%x}"
  if [[ ":${ZSH_EVAL_CONTEXT:-}:" == *:file:* ]]; then
    SOURCED=1
  else
    SOURCED=0
  fi
else
  SCRIPT_PATH="$0"
  SOURCED=0
fi

# Do not change the caller's shell options when this file is sourced.
if [ "$SOURCED" -eq 0 ]; then
  set -euo pipefail
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is required but was not found on PATH." >&2
  echo "Install uv, then run this script again." >&2
  if [ "$SOURCED" -eq 1 ]; then
    return 1
  fi
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

if ! cd "$PROJECT_ROOT"; then
  echo "Error: could not change to project directory: $PROJECT_ROOT" >&2
  if [ "$SOURCED" -eq 1 ]; then
    return 1
  fi
  exit 1
fi

if ! uv sync; then
  echo "Error: uv sync failed." >&2
  if [ "$SOURCED" -eq 1 ]; then
    return 1
  fi
  exit 1
fi

if [ "$SOURCED" -eq 0 ]; then
  echo "Virtual environment is ready at $PROJECT_ROOT/.venv"
  echo "To activate it in your current shell, run:"
  echo ". ./setup_venv.sh"
else
  # shellcheck source=/dev/null
  if ! . "$PROJECT_ROOT/.venv/bin/activate"; then
    echo "Error: could not activate the virtual environment." >&2
    return 1
  fi
  echo "Virtual environment activated: $VIRTUAL_ENV"
fi
