#!/home/m83393/.tmux/tmux-venv/bin/python3

import os
import logging
import socket
import datetime
import signal
import traceback
from pytimer import tmux_helper
from pytimer.pomodoro import PomodoroTimer
from pytimer.jira import JiraTimer

class PyTimerDaemon:
    CMDS = ["LIST", "STATUS"]
    PATH = "/tmp/tmux-pytimer/daemon"

    def __init__(self):
        self.init_logging(log_level=logging.DEBUG)

        if os.path.exists(f"{self.PATH}/pytimer.sock"):
            self.check_sock_alive(f"{self.PATH}/pytimer.sock")
        else:
            os.makedirs(self.PATH, exist_ok=True)

        # Define timers
        pomodoro = PomodoroTimer()
        jira = JiraTimer()

        # DEBUG
        jira.gen_tickets_menu()

        self.timers = {
            pomodoro.name: pomodoro,
            jira.name: jira
        }


    def init_logging(self, log_level=logging.INFO):
        if os.path.exists("/tmp/tmux-pytimer/daemon/") != True:
            os.makedirs("/tmp/tmux-pytimer/daemon/")

        logFormatter = logging.Formatter("[%(levelname)-8s]\t%(message)s")

        rootLogger = logging.getLogger()
        rootLogger.setLevel(log_level)

        fileHandler = logging.FileHandler(f"/tmp/tmux-pytimer/daemon/daemon.log")
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

        logging.info(f"Logging started {datetime.datetime.now()}")

    def check_sock_alive(self, socket_path):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            client.connect(socket_path)

            client.close()
        except ConnectionRefusedError:
            logging.info("Dead socket found, starting up server")
            return

        logging.warning("Daemon already running. Aborting duplicate startup")
        os._exit(0)


    def handle_daemon_command(self, cmd):
        logging.info(f"Received daemon command: {cmd['action']}")
        if cmd["action"] == "LIST":
            self.daemon_list()
        else:
            logging.warning(f"{cmd['action']} is a valid daemon command, but it is not implemented")
            return


    def daemon_list(self):
        options = []
        for timer in list(self.timers.values()):
            if timer.is_enabled:
                options.append(tmux_helper.menu_add_option(f"* {timer.name}", "", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py MENU --timer {timer.name}\""))
            else:
                options.append(tmux_helper.menu_add_option(f"  {timer.name}", "", f"run-shell \"{tmux_helper.get_plugin_dir()}/scripts/tmux_pytimer.py MENU --timer {timer.name}\""))

        tmux_helper.menu_create("Timers", "R", "S", options)

        return


    def daemon_stop(self):
        logging.info(f"Received STOP command. Quiting...")
        os.unlink(f"{self.PATH}/pytimer.sock")
        logging.info(f"Logging ended {datetime.datetime.now()}")
        os._exit(0)


    def handle_timer_command(self, cmd):
        logging.info(f"Received timer command: {cmd['action']} for {cmd['timer']}")
        if cmd["action"] == "MENU":
            self.timers[cmd['timer']].gen_menu()
        elif cmd["action"] == "TASKS":
            self.timers[cmd['timer']].get_tickets_menu()
        else:
            logging.warning(f"{cmd['action']} is a valid daemon command, but it is not implemented")
            return


    def validate_command(self, data):
        try:
            data = data.decode()
        except Exception as e:
            logging.warning(f"[{e.__class__.__name__}] Unable to decode message")
            return None

        try:
            logging.debug(f"Received: {data}")
            data = data.split(" ")

            timer_names = list(self.timers.keys())

            if len(data) > 2:
                logging.warning(f"{len(data)} arguments provided.\nDaemon commands require one positional argument ([CMD]) and Timer commands require two positional arguments ([CMD] [TIMER]).\n{data}")
                return None
            # Daemon Command
            elif len(data) == 1:
                cmd = data[0]
                if cmd not in self.CMDS:
                    logging.warning(f"{cmd} is not a valid daemon command. Valid daemon commands are: {self.CMDS}")
                    return None

                return {"type": "daemon", "cmd": {"action": cmd}}
            # Timer Command
            elif len(data) == 2:
                cmd = data[0]
                timer_name = data[1]

                if timer_name not in timer_names:
                    logging.warning(f"There is no timer named {timer_name}. Valid timers are: {timer_names}")
                    return None

                for timer in list(self.timers.values()):
                    if timer.name == timer_name:
                        if cmd not in timer.cmds:
                            logging.warning(f"{cmd} is not a valid command for {timer.name}. Valid commands for {timer.name} are: {timer.cmds}")
                        else:
                            return {"type": "timer", "cmd": {"action": cmd, "timer": timer_name}}

                return None
        except Exception as e:
            logging.warning(f"[{e.__class__.__name__}] Unable to decode message")


    def listen(self, server):
        connection, client_address = server.accept()

        try:
            logging.debug(f"Connection from {str(connection).split(', ')[0][-4:]}")

            while True:
                data = connection.recv(1024)
                if not data:
                    break

                message = f"ACK"
                connection.sendall(message.encode())

                command = self.validate_command(data)
                if command == None:
                    break

                if command["type"] == "daemon":
                    self.handle_daemon_command(command["cmd"])
                elif command["type"] == "timer":
                    self.handle_timer_command(command["cmd"])
                else:
                    logging.warning(f"Unknown command type {command['type']}.\n{command}")

            connection.close()
        except Exception:
            logging.critical(f"Encountered the folloing error when receiving data: {traceback.format_exc()}")
            connection.close()
            self.daemon_stop()


def signal_handler(sig, frame):
    logging.info(f"Received {signal.Signals(sig).name}. Quiting...")
    os.unlink("/tmp/tmux-pytimer/daemon/pytimer.sock")
    logging.info(f"Logging ended {datetime.datetime.now()}")
    os._exit(0)


def main():
    daemon = PyTimerDaemon()

    catchable_sigs = set(signal.Signals) - {signal.SIGKILL, signal.SIGSTOP, signal.SIGCHLD, signal.SIGINT}
    for sig in catchable_sigs:
        signal.signal(sig, signal_handler)

    try:
        os.unlink(f"{daemon.PATH}/pytimer.sock")
    except FileNotFoundError:
        pass
    except OSError:
        logging.critical("Unable to remove old socket")
        os._exit(0)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    server.bind(f"{daemon.PATH}/pytimer.sock")
    server.listen(1)
    logging.info(f"Daemon listening on {daemon.PATH}/pytimer.sock")

    if os.fork():
        # Tell the parent process to exit
        os._exit(0)

    while True:
        daemon.listen(server)

if __name__ == "__main__":
    main()
