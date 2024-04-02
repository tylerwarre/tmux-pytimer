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

SOCK_PATH = "/tmp/tmux-pytimer/daemon/pytimer.sock"
COMMANDS = multiprocessing.Queue()
TMUX_STATUS_KEY = "@pytimer-status"

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


def check_sock_alive():
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        client.connect(SOCK_PATH)

        client.close()
    except ConnectionRefusedError:
        logging.info("Dead socket found, starting up server")
        return

    logging.warning("Daemon already running. Aborting duplicate startup")
    os._exit(0)

class CmdHandler:
    def __init__(self) -> None:
        self.cmds = ["LIST", "STATUS", "STOP"]

        self.timers = {
            "Jira": JiraTimer(verify_tls=False, name="Jira"),
            "Test": JiraTimer(priority=100, name="Test", sessions=1, verify_tls=False)
        }


    def start(self):
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
        elif cmd["cmd"] == "STOP":
            self.daemon_stop()
        else:
            logging.warning(f"{cmd['cmd']} is a valid daemon command, but it is not implemented")


    def daemon_stop(self):
        logging.info(f"Received STOP command. Quiting...")
        os.unlink(SOCK_PATH)
        logging.info(f"Logging ended {datetime.datetime.now()}")
        os._exit(0)


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
        TmuxHelper.set_tmux_option(TMUX_STATUS_KEY, status)
        return


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
        value = None
        logging.debug(cmd)
        if cmd[-1] == "'":
            try:
                pos = cmd.index("'")
                value = cmd[pos+1:-1]
                cmd = cmd[:pos-1]
            except ValueError:
                logging.warning(f"Unclosed quotes in {cmd}")
                return False

        cmd = cmd.split(" ")

        if value != None:
            cmd.append(value)

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
            elif len(cmd) == 2:
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
        pass

    def start(self):
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

    if os.path.exists(SOCK_PATH):
        check_sock_alive()
    else:
        dir_path = SOCK_PATH.split("/")[:-1]
        dir_path = "/".join(dir_path) + "/"
        os.makedirs(dir_path, exist_ok=True)
    
    CmdHandler().start()
    SockDaemon().start()

if __name__ == "__main__":
    main()
