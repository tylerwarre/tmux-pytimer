#!/home/m83393/.tmux/tmux-venv/bin/python3

import os
import asyncio
import argparse
import socket
import logging
import datetime
import traceback
import multiprocessing
from pytimer import TmuxHelper
from pytimer.timers import JiraTimer

SOCK_PATH = "/tmp/tmux-pytimer/daemon"
COMMANDS = multiprocessing.Queue()

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
        #pomodoro = PomodoroTimer()
        jira = JiraTimer(verify_tls=False)
        jira2 = JiraTimer(priority=100, name="Test", sessions=1, verify_tls=False)

        self.timers = {
            jira.name: jira,
            jira2.name: jira2
        }

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


    def handle_daemon_command(self, cmd) -> list:
        response = ["ACK"]
        logging.info(f"Received daemon command: {cmd['action']}")

        if cmd["action"] == "LIST":
            self.daemon_list()
        elif cmd["action"] == "STATUS":
            response.insert(0, self.daemon_status())
        else:
            logging.warning(f"{cmd['action']} is a valid daemon command, but it is not implemented")

        return response


    def daemon_status(self):
        status = ""
        timers = list(self.timers.values())
        timers = sorted(timers, key=lambda timer: timer.priority)
        for timer in timers:
            if timer.state.enabled:
                result = timer.update()
                if type(result) != str:
                    logging.critical(f"update() for {timer.name} did not return a string")
                    continue

                status += result

        logging.debug(f"Updating status: {status}")
        return status


    def daemon_list(self):
        options = []
        for timer in list(self.timers.values()):
            if timer.state.enabled:
                options.append(TmuxHelper.menu_add_option(f"* {timer.name}", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py MENU --timer {timer.name} --blocking\""))
            else:
                options.append(TmuxHelper.menu_add_option(f"  {timer.name}", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py MENU --timer {timer.name} --blocking\""))

        TmuxHelper.menu_create("Timers", "R", "S", options)

        return


    def daemon_stop(self):
        logging.info(f"Received STOP command. Quiting...")
        os.unlink(f"{self.PATH}/pytimer.sock")
        logging.info(f"Logging ended {datetime.datetime.now()}")
        os._exit(0)


    def handle_timer_command(self, cmd) -> list:
        response = ["ACK"]
        logging.info(f"Received timer command: {cmd['action']} for {cmd['timer']}")

        if cmd["action"] == "MENU":
            self.timers[cmd['timer']].gen_menu()
        elif cmd["action"] == "TASKS":
            self.timers[cmd['timer']].gen_tickets_menu()
        elif cmd["action"] == "START":
            self.timers[cmd['timer']].start()
        elif cmd["action"] == "STOP":
            self.timers[cmd['timer']].stop()
        elif cmd["action"] == "PAUSE":
            self.timers[cmd['timer']].pause()
        elif cmd["action"] == "RESUME":
            self.timers[cmd['timer']].resume()
        elif cmd["action"] == "SET":
            self.timers[cmd['timer']].set_task(cmd['value'])
        elif cmd["action"] == "COMMENT":
            self.timers[cmd['timer']].comment(cmd['value'])
        else:
            logging.warning(f"{cmd['action']} is a valid daemon command, but it is not implemented")

        return response


    def validate_command(self, data):
        try:
            data = data.decode()
        except Exception as e:
            logging.warning(f"[{e.__class__.__name__}] Unable to decode message")
            return None

        try:
            logging.debug(f"Received: {data}")
            data = data.split(" ")
            if "BLOCK" in data:
                data.remove("BLOCK")
                block = True
            else:
                block = False

            timer_names = list(self.timers.keys())

            if len(data) > 3:
                logging.warning(f"{len(data)} arguments provided.\nDaemon commands require one positional argument ([CMD]) and Timer commands require two positional arguments ([CMD] [TIMER]).\n{data}")
                return None
            # Daemon Command
            elif len(data) == 1:
                cmd = data[0]
                if cmd not in self.CMDS:
                    logging.warning(f"{cmd} is not a valid daemon command. Valid daemon commands are: {self.CMDS}")
                    return None

                return {"type": "daemon", "cmd": {"action": cmd, "blocking": block}}
            # Timer Command
            elif len(data) >= 2:
                cmd = data[0]
                timer_name = data[1]
                if len(data) == 3:
                    value = data[2]
                else:
                    value = None

                if timer_name not in timer_names:
                    logging.warning(f"There is no timer named {timer_name}. Valid timers are: {timer_names}")
                    return None

                for timer in list(self.timers.values()):
                    if timer.name == timer_name:
                        if cmd not in timer.cmds:
                            logging.warning(f"{cmd} is not a valid command for {timer.name}. Valid commands for {timer.name} are: {timer.cmds}")
                        else:
                            if len(data) == 2:
                                return {"type": "timer", "cmd": {"action": cmd, "timer": timer_name, "blocking": block}}
                            elif value != None:
                                return {"type": "timer", "cmd": {"action": cmd, "timer": timer_name, "value": value, "blocking": block}}

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

                command = self.validate_command(data)
                if command == None:
                    break

                if command["cmd"]["blocking"]:
                    message = f"SYN ACK;"
                    connection.sendall(message.encode())
                    logging.debug(f"Sent: {message}")

                if command["type"] == "daemon":
                    response = self.handle_daemon_command(command["cmd"])
                elif command["type"] == "timer":
                    response = self.handle_timer_command(command["cmd"])
                else:
                    response = ["ACK"]
                    logging.warning(f"Unknown command type {command['type']}.\n{command}")

                for msg in response:
                    msg += ";"
                    connection.sendall(msg.encode())
                    logging.debug(f"Sent: {msg[:-1]}")

            connection.close()
        except Exception:
            logging.critical(f"Encountered the folloing error when receiving data: {traceback.format_exc()}")
            connection.close()
            self.daemon_stop()

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

class CmdHandler:
    def __init__(self) -> None:
        self.cmds = ["LIST", "STATUS"]

        self.timers = {
            "Jira": JiraTimer(verify_tls=False, name="Jira"),
            "Test": JiraTimer(priority=100, name="Test", sessions=1, verify_tls=False)
        }
        multiprocessing.Process(target=self.cmd_handler).start()


    def cmd_handler(self):
        while True:
            cmd = COMMANDS.get()
            logging.debug(f"Processing: {cmd}")
            cmd = self.validate_cmd(cmd)

            if type(cmd) != dict:
                continue

            if "timer" in cmd:
                self.timer_cmd_handler(cmd)
            elif "cmd" in cmd:
                self.daemon_cmd_handler(cmd)
            else:
                logging.warning(f"Invalid cmd: {cmd}")
                continue

    def daemon_cmd_handler(self, cmd):
        if cmd["cmd"] == "LIST":
            self.daemon_list()
        elif cmd["cmd"] == "STATUS":
            self.daemon_status()
        else:
            logging.warning(f"{cmd['cmd']} is a valid daemon command, but it is not implemented")


    def daemon_list(self):
        options = []
        for timer in list(self.timers.values()):
            if timer.state.enabled:
                options.append(TmuxHelper.menu_add_option(f"* {timer.name}", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py MENU --timer {timer.name}\""))
            else:
                options.append(TmuxHelper.menu_add_option(f"  {timer.name}", "", f"run-shell \"{TmuxHelper.get_plugin_dir()}/scripts/tmux_pytimer.py MENU --timer {timer.name}\""))

        TmuxHelper.menu_create("Timers", "R", "S", options)

        return


    def daemon_status(self):
        status = ""
        timers = list(self.timers.values())
        timers = sorted(timers, key=lambda timer: timer.priority)
        for timer in timers:
            if timer.state.enabled:
                result = timer.update()
                if type(result) != str:
                    logging.critical(f"update() for {timer.name} did not return a string")
                    continue

                status += result

        logging.debug(f"Updating status: {status}")
        return status


    def timer_cmd_handler(self, cmd):
        if cmd["cmd"] == "MENU":
            self.timers[cmd['timer']].gen_menu()
        elif cmd["cmd"] == "TASKS":
            self.timers[cmd['timer']].gen_tickets_menu()
        elif cmd["cmd"] == "START":
            self.timers[cmd['timer']].start()
        elif cmd["cmd"] == "STOP":
            self.timers[cmd['timer']].stop()
        elif cmd["cmd"] == "PAUSE":
            self.timers[cmd['timer']].pause()
        elif cmd["cmd"] == "RESUME":
            self.timers[cmd['timer']].resume()
        elif cmd["cmd"] == "SET":
            self.timers[cmd['timer']].set_task(cmd['value'])
        elif cmd["cmd"] == "COMMENT":
            self.timers[cmd['timer']].comment(cmd['value'])
        else:
            logging.warning(f"{cmd['cmd']} is a valid daemon command, but it is not implemented")


    def validate_cmd(self, cmd) -> dict|bool:
        cmd = cmd.split(" ")

        # daemon command
        if len(cmd) == 1:
            cmd = cmd[0]
            if cmd not in self.cmds:
                logging.warning(f"{cmd} is not a valid daemon command")
                return False

            cmd = {"cmd": cmd}
            return cmd
        # timer command
        elif len(cmd) >= 2:
            if len(cmd) > 3:
                logging.warning(f"Timer commands can not have more than 3 arguments, "\
                        f"but {len(cmd)} provided.\n{cmd}")
                return False
            elif len == 2:
                value = None
                timer = cmd[1]
                cmd = cmd[0]
            else:
                value = cmd[2]
                timer = cmd[1]
                cmd = cmd[0]

            if timer not in self.timers:
                logging.warning(f"{timer} is not a timer instance")
                return False

            if cmd not in self.timers[timer].cmds:
                logging.warning(f"{cmd} is not a valid timer command for {timer}")
                return False

            cmd = {"cmd": cmd, "timer": timer, "value": value}
            return cmd
        else:
            logging.warning(f"Invalid cmd: {cmd}")
            return False


            
class SockDaemon:
    def __init__(self):
        asyncio.run(self.sock_server())

    async def sock_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        msg = (await reader.read(1024))

        if not msg:
            writer.close()
            return

        msg = msg.decode().rstrip()
        cmds = msg.split(";")
        cmds = cmds[:-1]

        for cmd in cmds:
            COMMANDS.put(cmd)
            logging.debug(f"Received: {cmd}")

        writer.write("ACK".encode())
        writer.close()


    async def sock_server(self):
        server = await asyncio.start_unix_server(self.sock_handler, SOCK_PATH)
        async with server:
            await server.serve_forever()

def main():
    init_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        init_logging(log_level=logging.DEBUG)
    else:
        init_logging()
        if os.fork():
            # Tell the parent process to exit
            os._exit(0)
    
    CmdHandler()
    SockDaemon()

if __name__ == "__main__":
    main()
