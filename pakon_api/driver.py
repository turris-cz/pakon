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
    except Exception as e:
        error.append(f"cannot read from pakon-socket, is service running? {e}")
    finally:
        sock.close()

    try:
        data = json.loads(response)
    except Exception as e:
        error.append(f"no response data. {e}")

    return data, error
