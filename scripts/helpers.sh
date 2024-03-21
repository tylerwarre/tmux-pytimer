#!/usr/bin/env bash

get_tmux_option() {
    local option=$1
    local default_value=$2

    option_value=$(tmux show-option -gqv "$option")
    if [[ -z "$option_value" ]]; then
        echo "$default_value"
    else
        echo "$option_value"
    fi
}

set_tmux_option() {
    local option="$1"
    local value="$2"

    tmux set-option -g "$option" "$value"
}

interpolate_status() {
    local status
    local interpolated_status="\#{pytimer_status}"
    local status_line="#($CURRENT_DIR/scripts/tmux_pytimer.py STATUS)"
    echo "$status_line"

    status=$(get_tmux_option "status-right" "-1")
    if [[ "$status" == "-1" ]]; then
        echo "status-right returned no value from tmux"
        exit
    fi
    status="${status/$interpolated_status/$status_line}"
    set_tmux_option "status-right" "$status"
}
