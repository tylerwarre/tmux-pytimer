#!/home/m83393/.tmux/tmux-venv/bin/python3

import os
import socket
import argparse
from pytimer import TmuxHelper

# TODO fix STATUS command which crashes the daemon when STATUS data is returned. Likley and issue with the SYN/ACK process
    # Issue is related to race condition. See whiteboard. Probably best to create a SM at this point. Also see whiteboard
# TODO create a state machine that manages the SYN/ACK state, the command sent, and whether data should be expected

def receive_msg(socket: socket.socket, buff_size=1024):
    response = socket.recv(buff_size)
    response = response.decode()
    response = response.split(";")

    messages = []
    num_msgs = len(response)
    i = 0
    while i < num_msgs:
        if i+1 < num_msgs:
            if response[i] != "SYN ACK" and response[i+1] == "ACK":
                messages.append((response[i], response[i+1]))
                i += 1
            else:
                messages.append(response[i])
        else:
            messages.append(response[i])

        i += 1

    return messages


def send_daemon_cmd(args):
    socket_path = "/tmp/tmux-pytimer/daemon/pytimer.sock"

    if not os.path.exists(socket_path):
        TmuxHelper.message_create(f"Socket does not exists at {socket_path}. Has the daemon started?")
        return

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if args.blocking:
        client.settimeout(300)
    else:
        client.settimeout(3)

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
            messages = receive_msg(client)

            msg = messages.pop(0)
            if msg != "SYN ACK":
                TmuxHelper.message_create(f"SYN ACK expected for a blocking command, but recieved: {msg}")
                return

            while True:
                value = None
                if len(messages) > 0:
                    msg = messages.pop(0)
                else:
                    messages = receive_msg(client)
                    msg = messages.pop(0)

                if msg == "ACK":
                    break

                value = msg

                #if value != None:
                #    print(value)
        else:
            messages = receive_msg(client)

            for msg in messages:
                value = None
                msg = messages.pop(0)
                if type(msg) == tuple:
                    value, msg = msg
                    
                if msg != "ACK":
                    TmuxHelper.message_create(f"ACK expected, but recieved: {msg}")

                if value != None:
                    print(value)


        client.close()
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
    #    os._exit(0)

    send_daemon_cmd(args)

    return 0

if __name__ == '__main__':
    main()
