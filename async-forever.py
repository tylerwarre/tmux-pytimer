import multiprocessing
from re import sub
import socketserver
import subprocess

# Create a semaphore that is initalized in each timer
# daemon functions requires a lock on all semaphores
# Certain tmux functions should have a semaphore
# Add a handle_cmd() function to each timer that calls the appropriate command's method with multiprocessing.Process and set the approrpriate timerouts
# Create a chart for each function whether it should be blocking and a reasonable timeout

s_timer = multiprocessing.Semaphore()

def worker(cmd, sock):
    if cmd == "test":
        thread = multiprocessing.Process(target=tmux, args=[cmd], daemon=True, name=cmd)
        thread.start()
    else:
        thread = multiprocessing.Process(target=jira, args=[cmd], daemon=True, name=cmd)
        thread.start()
        thread.join()

        if thread.exitcode != 0:
            print(f"Unable to complete {cmd}")
            thread.terminate()
            s_timer.release()

    sock.request.sendall(cmd.encode())
    multiprocessing.active_children()

def tmux(cmd):
    s_timer.acquire(block=True)
    subprocess.run(["tmux", "display-popup", "hello world"])
    print(f"Tmux: {cmd}")
    s_timer.release()

def jira(cmd):
    s_timer.acquire(block=True)
    print(f"Jira: {cmd}")
    s_timer.release()

class ThreadedUnixRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = str(self.request.recv(1024), 'ascii')
        worker(data, self)

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    #threading.Thread(target=worker, daemon=True).start()

    # Create the server, binding to localhost on port 9999
    with socketserver.ThreadingUnixStreamServer("/tmp/my.socket", ThreadedUnixRequestHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
