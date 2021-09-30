from socket import socket, AF_UNIX, SOCK_STREAM

import json


def pakon_socket(query):
    error = []
    data = []
    sock = socket(AF_UNIX, SOCK_STREAM)
    try:
        sock.connect("/var/run/pakon-query.sock")
        sock.sendall(query)
        with sock.makefile() as f:
            response = f.readline().strip()
    except:
        error.append("cannot read from pakon-socket, is service running?")
    finally:
        sock.close()

    try:
        data = json.loads(response)
    except:
        error.append("no response data")

    return data, error
