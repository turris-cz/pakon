from socket import socket, AF_UNIX, SOCK_STREAM
from contextlib import contextmanager

@contextmanager
def pakon_socket():
    s = socket(AF_UNIX, SOCK_STREAM)
    s.connect("/var/run/pakon-query.sock")
    yield s
    s.close()
