from typing import Iterable, List, Union
from euci import EUci, UciExceptionNotFound

import subprocess
from contextlib import AbstractContextManager, contextmanager

__all__ = ["INTERVALS", "uci_get", "iter_section", "open_process", "Objson"]

INTERVALS = {"M": 60, "H": 3600, "D": 24 * 3600, "W": 7 * 24 * 3600}


def uci_get(config, *options, **kwargs) -> Union[str, int, bool]:
    """Specify `dtype` kwarg if you need `int` without further conversion."""
    with EUci() as uci:
        ret = uci.get(config, *options, **kwargs)
    return ret


def iter_section(config: str, section: str) -> Iterable[dict]:
    """Iterate anonymous sections
    If we want to iterate throught multiple sections
    for `pakon.@archive_rule[0-n]` the parameters would be
    config='pakon'pakon, section='archive_rule'."""
    section = f"{config}.@{section}"
    i = 0
    uci = EUci()
    while True:
        try:
            yield uci.get_all(section + f"[{i}]")
            i += 1
        except UciExceptionNotFound:
            break
    return StopIteration


@contextmanager
def open_process(command: List[str]):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    yield proc
    proc.terminate()


class Objson:  # json -> object
    """Dict structure to Object with attributes"""
    def __init__(self, __data) -> None:
        self.__dict__= {
            key: Objson(val) if isinstance(val,dict)
            else val for key, val in __data.items()
        }

    def __repr__(self) -> str:
        return str(self.__dict__)
