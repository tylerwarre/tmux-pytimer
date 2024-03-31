import pickle
import multiprocessing
from os import unlink
from datetime import datetime, timedelta
import socket

# The handle function must continue to run until the socket it pulled from the Queue. Otherwise the socket returns ConnectionClosed
# Add a pipe for the handle function that connects to the handle_cmds functions. When the socket is pulled from the queue send a message back through the pipe to tell the handle() function to exit
# Use aync/yeild to limit CPU usage while waiting for socket to get pulled from Queue

# can we create a queue of handle() calls so that we can put all of the commands in a Queue?

# Create a semaphore that is initalized in each timer
# daemon functions requires a lock on all semaphores
# Certain tmux functions should have a semaphore
# Add a handle_cmd() function to each timer that calls the appropriate command's method with multiprocessing.Process and set the approrpriate timerouts
# Create a chart for each function whether it should be blocking and a reasonable timeout

SOCK_PATH = "/tmp/my.socket"
commands = multiprocessing.Queue()
s_jira = multiprocessing.Semaphore(1)

def handle(s):
    data = s.recv(1024)

    if not data:
        s.close()
        return

    data = data.decode().rstrip()
    commands.put((data, s))
    done = datetime.now() + timedelta(seconds=10)
    while datetime.now() < done:
        pass
    return 0

def jira(cmd, s):
    done = datetime.now() + timedelta(seconds=10)
    while datetime.now() < done:
        continue
    print(cmd)
    s.shutdown(socket.SHUT_RDWR)
    s.close()

    return 0

def tmux(cmd, s):
    print(cmd)
    s.shutdown(socket.SHUT_RDWR)
    s.close()

    return 0

def process_cmds():
    while True:
        multiprocessing.active_children()
        cmd, s = commands.get()
        print(cmd)
        print(f"processing: {cmd}")

        if cmd == "jira":
            s_jira.acquire()
            task = multiprocessing.Process(target=jira, args=[cmd,s,], daemon=True)
            task.start()
            task.join(timeout=15)
            if task.is_alive():
                print(f"Unable to process {cmd}")
                task.terminate()
                s_jira.release()
            else:
                s_jira.release()
        elif cmd == "tmux":
            s_jira.acquire()
            task = multiprocessing.Process(target=tmux, args=[cmd,s,], daemon=True)
            task.start()
            task.join(timeout=3)
            if task.is_alive():
                print(f"Unable to process {cmd}")
                task.terminate()
                s_jira.release()
            else:
                s_jira.release()


multiprocessing.Process(target=process_cmds).start()
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
unlink(SOCK_PATH)
sock.bind(SOCK_PATH)
sock.listen(4)
commands.put(("test", "hello"))
msg1, msg2 = commands.get()
print(f"{msg1}, {msg2}")

while True:
    multiprocessing.active_children()
    s, addr = sock.accept()
    multiprocessing.Process(target=handle, args=[s,], daemon=True).start()
