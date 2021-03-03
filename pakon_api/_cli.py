import subprocess
from typing import List

from pakon_api.utils import utilParser

_MASTER_COMMAND = ['/usr/bin/pakon-show']


def _run_show(filters) -> List[str]:
    _command = _MASTER_COMMAND + utilParser.unwrap_query(filters)

    result = subprocess.run(_command, capture_output=True)
    return result.stdout.decode().split('\n')
