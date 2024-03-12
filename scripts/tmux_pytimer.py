#!/usr/bin/env python

import urllib3
import argparse
from timers import timer

# TODO Program should create a "daemon" that waits commands. Timers should only be instatiated once

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timer', help="Specify the name of the timer the command refers to")
    parser.add_argument('--action', help="Specify the message you would like to display")
    args = parser.parse_args()

    init_logging()
    urllib3.disable_warnings()

    my_timer = timer.PasswordSpray()
    my_timer.gen_menu()

    return 0

if __name__ == '__main__':
    main()
