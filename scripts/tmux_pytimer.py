#!/home/m83393/.tmux/tmux-venv/bin/python3

import sys
import os
import socket
import argparse
from pytimer import TmuxHelper, DaemonStates

def send_daemon_cmd(args):
    socket_path = "/tmp/tmux-pytimer/daemon/pytimer.sock"

    if not os.path.exists(socket_path):
        TmuxHelper.message_create(f"Socket does not exists at {socket_path}. Has the daemon started?")
        return

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(300)

    try:
        client.connect(socket_path)

        if args.timer != None and args.value != None:
            message = f"{args.cmd} {args.timer} {args.value}"
        elif args.timer == None:
            message = f"{args.cmd}"
        else:
            message = f"{args.cmd} {args.timer}"

        if args.blocking:
            message += " BLOCK"

        client.sendall(message.encode())

        if args.blocking:
            state = DaemonStates.SynAck(client)
        else:
            state = DaemonStates.Ack(client)

        while True:
            if str(state) == "Done":
                break

            next_state = state.next()
            if next_state != None:
                state = next_state

    except TimeoutError:
        TmuxHelper.message_create("Timeout while waiting for ACK from daemon")
    except ConnectionRefusedError:
        TmuxHelper.message_create("Socket is not listening. Has the daemon started?")
    except Exception as e:
        TmuxHelper.message_create(f"{e.__class__.__name__}: Unable to connect to socket")

    return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timer', help="Specify the name of the timer the command refers to")
    parser.add_argument('--value', help="Specify the optional value for the command")
    parser.add_argument('--blocking', action="store_true", help="Specify the optional value for the command")
    parser.add_argument('cmd', help="Specify the command you would like to perform")
    args = parser.parse_args()

    #if os.fork():
    #    # Tell the parent process to exit
    #    sys.exit(0)

    send_daemon_cmd(args)

    return 0

if __name__ == '__main__':
    main()
