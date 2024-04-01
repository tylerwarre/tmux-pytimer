import os
import time
import math
import asyncio
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import socket

# switch to asyncio for socket server sigh... (https://stackoverflow.com/questions/48506460/python-simple-socket-client-server-using-asyncio)

# use if asyncio doesn't work out
# The handle function must continue to run until the socket it pulled from the Queue. Otherwise the socket returns ConnectionClosed
# Add a pipe for the handle function that connects to the handle_cmds functions. When the socket is pulled from the queue send a message back through the pipe to tell the handle() function to exit
# Use aync/yeild to limit CPU usage while waiting for socket to get pulled from Queue

# Create a semaphore that is initalized in each timer
# daemon functions requires a lock on all semaphores
# Certain tmux functions should have a semaphore
# Add a handle_cmd() function to each timer that calls the appropriate command's method with multiprocessing.Process and set the approrpriate timerouts
# Create a chart for each function whether it should be blocking and a reasonable timeout

SOCK_PATH = "/tmp/my.socket"
commands = multiprocessing.Queue()
s_jira = multiprocessing.Semaphore(1)
s_tmux = multiprocessing.Semaphore(1)

async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    cmd = (await reader.read(1024))

    if not cmd:
        writer.close()
        return

    cmd = cmd.decode().rstrip()
    commands.put(cmd)

    logging.warning(f"Added {cmd} to queue")
    writer.write("ACK".encode())
    writer.close()

def jira(cmd):
    data = [math.sqrt(i) for i in range(50000000)]

    logging.warning(cmd)
    return

def tmux(cmd):
    data = [math.sqrt(i) for i in range(50000000)]

    logging.warning(cmd)
    return

def daemon(cmd):
    logging.warning(cmd)
    return

def cmd_processor():
    while True:
        cmd = commands.get()
        logging.warning(f"Processing {cmd}")
        if cmd == "daemon":
            daemon(cmd)
        elif cmd == "jira":
            jira(cmd)
        elif cmd == "tmux":
            tmux(cmd)
        else:
            logging.warning(f"Unkown command: {cmd}")


async def sock_server():
    server = await asyncio.start_unix_server(handle, SOCK_PATH)
    async with server:
        await server.serve_forever()

if __name__ == '__main__':

    if os.fork():
        os._exit(0)

    loop = asyncio.get_event_loop()
    multiprocessing.Process(target=cmd_processor).start()
    loop.create_task(sock_server())
    loop.run_forever()

