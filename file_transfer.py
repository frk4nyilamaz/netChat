import os

MAX_SIZE = 5 * 1024 * 1024 
BUFFER_SIZE = 1024  

def is_file_valid(filepath):
    return os.path.isfile(filepath) and os.path.getsize(filepath) <= MAX_SIZE

def get_file_size(filepath):
    return os.path.getsize(filepath)

def send_file(sock, filepath):
    filesize = os.path.getsize(filepath)
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            sock.sendall(chunk)
    return filesize

def receive_file(sock, filepath, filesize):
    received = 0
    with open(filepath, 'wb') as f:
        while received < filesize:
            chunk = sock.recv(min(BUFFER_SIZE, filesize - received))
            if not chunk:
                break
            f.write(chunk)
            received += len(chunk)
    return received 