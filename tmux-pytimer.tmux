#!/usr/bin/env bash

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
tmux bind-key y run-shell "$CURRENT_DIR/scripts/tmux_pytimer.py"
"$CURRENT_DIR/scripts/pytimer_daemon.py" &
