import subprocess
from typing import List

_MASTER_COMMAND = ['/usr/bin/pakon-show']

COMMANDS = {
    "page": "-p",
    "number": "-n"
}


def run_show(args) -> List[str]:
    _command = _MASTER_COMMAND + args

    result = subprocess.run(_command, capture_output=True)
    return result.stdout.decode().split('\n')
