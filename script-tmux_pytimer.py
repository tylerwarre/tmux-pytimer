#!/home/m83393/.tmux/tmux-venv/bin/python3

import os
import socket
import logging
import urllib3
import argparse
import datetime
import subprocess
import pytimer.tmux_helper as tmux_helper

# TODO Program should create a "daemon" that waits commands. Timers should only be instatiated once. Try creating a Unix socket server that is called whenever tmux refreshes, but does not start if it is already running

def send_daemon_cmd(cmd, timer):
    socket_path = "/tmp/tmux-pytimer/daemon/pytimer.sock"

    if not os.path.exists(socket_path):
        tmux_helper.message_create(f"Socket does not exists at {socket_path}. Has the daemon started?")
        return

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(socket_path)

    message = f"{cmd} {timer}"
    client.sendall(message.encode())

    response = client.recv(1024)
    logging.info(f"Received date: {response.decode()}")

    client.close()

def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--timer', help="Specify the name of the timer the command refers to")
    # parser.add_argument('--action', help="Specify the message you would like to display")
    # args = parser.parse_args()

    # urllib3.disable_warnings()

    # my_timer = timer.PasswordSpray()
    # my_timer.gen_menu()

    send_daemon_cmd("START", "PasswordSpray")

    return 0

if __name__ == '__main__':
    main()
