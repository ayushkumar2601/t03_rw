#!/usr/bin/env bash
# Run both Task 03 Backend and Frontend concurrently
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Activate venv if it exists
if [ -d "$DIR/.venv" ]; then
    source "$DIR/.venv/bin/activate"
fi

python3 "$DIR/run.py"
