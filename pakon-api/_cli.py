import subprocess
from typing import List

def _run_show() -> List[str]:
    result = subprocess.run('/usr/bin/pakon-show', capture_output=True)
    return result.stdout.decode().split('\n')
