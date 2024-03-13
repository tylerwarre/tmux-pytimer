#!/usr/bin/env bash

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
date >> /tmp/tmux-pytimer/daemon/daemon.log
tmux bind-key y run-shell "$CURRENT_DIR/scripts/tmux_pytimer.py"
