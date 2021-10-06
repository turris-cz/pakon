from typing import Iterable, Union
from euci import EUci, UciExceptionNotFound

INTERVALS = {"M": 60, "H": 3600, "D": 24 * 3600, "W": 7 * 24 * 3600}


def uci_get(*options, **kwargs) -> Union[str, int, bool]:
    """Specify `d_type` if you need `int` without further conversion."""
    with EUci() as uci:
        ret = uci.get(*options, **kwargs)
    return ret


def itersect(config: str, section: str) -> Iterable[dict]:
    """Iterate anonymous sections
    If we want to itearate throught multiple sections
    for `pakon.@archive_rule[1-n]` the parameters would be
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
