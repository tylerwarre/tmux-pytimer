#!/home/m83393/.tmux/tmux-venv/bin/python3

import os
import socket
import logging
import urllib3
import argparse
import datetime

# TODO Program should create a "daemon" that waits commands. Timers should only be instatiated once. Try creating a Unix socket server that is called whenever tmux refreshes, but does not start if it is already running

def init_logging(log_level=logging.INFO):
    if os.path.exists("/tmp/tmux-pytimer/") != True:
        os.makedirs("/tmp/tmux-pytimer/")

    logFormatter = logging.Formatter("[%(levelname)-8s]\t%(message)s")

    rootLogger = logging.getLogger()
    rootLogger.setLevel(log_level)

    fileHandler = logging.FileHandler("/tmp/tmux-pytimer/pytimer.log")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    logging.info(f"Logging started {datetime.datetime.now()}")

def send_daemon_cmd(cmd, timer):
    socket_path = "/tmp/tmux-pytimer/daemon/pytimer.sock"

    if not os.path.exists(socket_path):
        logging.warning(f"Socket does not exists at {socket_path}. Has the daemon started?")
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
