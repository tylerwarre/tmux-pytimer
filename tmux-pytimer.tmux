#!/usr/bin/env bash

#TODO add function that overwrites all she-bangs with a user specified python interpreter

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source "$CURRENT_DIR/scripts/helpers.sh"

tmux bind-key t run-shell "$CURRENT_DIR/scripts/tmux_pytimer.py LIST --blocking"

interpolate_status
#"$CURRENT_DIR/scripts/pytimer_daemon.py" &
