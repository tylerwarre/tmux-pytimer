import multiprocessing
from os import unlink
from datetime import datetime, timedelta
import socket

# Create a semaphore that is initalized in each timer
# daemon functions requires a lock on all semaphores
# Certain tmux functions should have a semaphore
# Add a handle_cmd() function to each timer that calls the appropriate command's method with multiprocessing.Process and set the approrpriate timerouts
# Create a chart for each function whether it should be blocking and a reasonable timeout

SOCK_PATH = "/tmp/my.socket"
commands = multiprocessing.Queue()
s_jira = multiprocessing.Semaphore(1)

def handle(conn):
    data = conn.recv(1024)

    if not data:
        conn.close()
        return

    data = data.decode().rstrip()
    commands.put(data)
    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
    return 0

def jira(cmd):
    done = datetime.now() + timedelta(seconds=10)
    while datetime.now() < done:
        continue
    print(cmd)

    return 0

def tmux(cmd):
    print(cmd)
    return 0

def process_cmds():
    while True:
        multiprocessing.active_children()
        cmd = commands.get()
        print(f"processing: {cmd}")

        if cmd == "jira":
            s_jira.acquire()
            task = multiprocessing.Process(target=jira, args=[cmd,], daemon=True)
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
            task = multiprocessing.Process(target=tmux, args=[cmd,], daemon=True)
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

while True:
    multiprocessing.active_children()
    conn, addr = sock.accept()
    multiprocessing.Process(target=handle, args=[conn,], daemon=True).start()
