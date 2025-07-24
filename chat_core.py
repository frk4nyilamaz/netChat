import threading

clients = {}
lock = threading.Lock()

def add_client(nickname, client_socket):
    with lock:
        clients[nickname] = client_socket

def remove_client(nickname):
    with lock:
        if nickname in clients:
            del clients[nickname]

def get_clients():
    with lock:
        return dict(clients)

def broadcast(message, sender_socket=None):
    with lock:
        for client, sock in clients.items():
            if sock != sender_socket:
                try:
                    sock.send((message + '\n').encode())
                except:
                    pass

def is_nickname_taken(nickname):
    with lock:
        return nickname in clients

def get_userlist():
    with lock:
        return list(clients.keys())

def get_socket_by_nickname(nickname):
    with lock:
        return clients.get(nickname) 