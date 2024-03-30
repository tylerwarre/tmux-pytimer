import socket
import threading
import queue
import socketserver

def client(path, message):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(path)
        sock.sendall(bytes(message, 'ascii'))
        msg = sock.recv(1024)
        print(f"{message}: {msg}")

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 9999
    
    threading.Thread(target=client, args=["/tmp/my.socket", "test",]).start()
    threading.Thread(target=client, args=["/tmp/my.socket", "my message",]).start()
    threading.Thread(target=client, args=["/tmp/my.socket", "my message",]).start()
    threading.Thread(target=client, args=["/tmp/my.socket", "my message",]).start()
    threading.Thread(target=client, args=["/tmp/my.socket", "my message",]).start()
    threading.Thread(target=client, args=["/tmp/my.socket", "my message",]).start()
