#!/home/m83393/.tmux/tmux-venv/bin/python3

import os
import logging
import socket
import datetime
import signal
from pytimer.pomodoro import PomodoroTimer

VALID_TIMERS = []

def signal_handler(sig, frame):
    logging.info(f"Received {signal.Signals(sig).name}. Quiting...")
    os.unlink("/tmp/tmux-pytimer/daemon/pytimer.sock")
    logging.info(f"Logging ended {datetime.datetime.now()}")
    os._exit(0)

def init_logging(log_level=logging.INFO):
    if os.path.exists("/tmp/tmux-pytimer/daemon/") != True:
        os.makedirs("/tmp/tmux-pytimer/daemon/")

    logFormatter = logging.Formatter("[%(levelname)-8s]\t%(message)s")

    rootLogger = logging.getLogger()
    rootLogger.setLevel(log_level)

    fileHandler = logging.FileHandler(f"/tmp/tmux-pytimer/daemon/daemon.log")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    logging.info(f"Logging started {datetime.datetime.now()}")


def check_sock_alive(socket_path):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        client.connect(socket_path)

        client.close()
    except ConnectionRefusedError:
        logging.info("Dead socket found, starting up server")
        return

    logging.warning("Daemon already running. Aborting duplicate startup")
    os._exit(0)


def main():
    init_logging()

    catchable_sigs = set(signal.Signals) - {signal.SIGKILL, signal.SIGSTOP, signal.SIGCHLD}
    for sig in catchable_sigs:
        signal.signal(sig, signal_handler)

    socket_path = "/tmp/tmux-pytimer/daemon/pytimer.sock"

    if os.path.exists(socket_path):
        check_sock_alive(socket_path)

    pomodoro = PomodoroTimer()
    #VALID_TIMERS.append(pomodoro.name)

    logging.info(f"Loaded timer classes: {VALID_TIMERS}")

    try:
        os.unlink(socket_path)
    except OSError:
        if os.path.exists(socket_path):
            raise

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    server.bind(socket_path)
    server.listen(1)
    logging.info(f"Daemon listening on {socket_path}")

    if os.fork():
        os._exit(0)

    while True:
        connection, client_address = server.accept()

        try:
            logging.info(f"Connection from {str(connection).split(', ')[0][-4:]}")

            while True:
                data = connection.recv(1024)
                if not data:
                    break

                data = data.decode()
                logging.info(f"Received data: {data}")
                connection.sendall("ACK".encode())

                data = data.split(" ")
                pomodoro.gen_menu()


            connection.close()
        except Exception as e:
            logging.critical(f"Encountered the folloing error when receiving data: {e.__traceback__}")
            connection.close()
            os.unlink(socket_path)
            logging.info(f"Daemon closed")
            break

    logging.info(f"Logging ended {datetime.datetime.now()}")
    return 0

if __name__ == "__main__":
    main()
