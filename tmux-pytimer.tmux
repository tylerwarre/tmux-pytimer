#!/usr/bin/env bash

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ $(/usr/bin/env) != *"${HOME}/tmux/tmux-venv"* ]]; then
    source "${HOME}/.tmux/tmux-venv/bin/activate"
    tmux dispay-message "activating venv"
fi
tmux bind-key y run-shell "$CURRENT_DIR/scripts/tmux-pytimer.py"
