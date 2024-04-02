#!/usr/bin/env bash

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source "$CURRENT_DIR/scripts/helpers.sh"

tmux bind-key t run-shell "$CURRENT_DIR/scripts/tmux_pytimer.py LIST"

interpolate_status
#"$CURRENT_DIR/scripts/pytimer_daemon.py" &
