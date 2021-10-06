import argparse
import time
import datetime
import re
from typing import Optional, Tuple

from ..utils import INTERVALS


# split value and unit
# regex.findall(string) -> [(<value>, <unit>)]
_TIMESPEC_GENERAL = re.compile(r"^([0-9]+)([WDHMwdhm]?)$")
_PATTERNS = ["%d-%m-%YT%H:%M:%S", "%d-%m-%Y"]


def _datetime_parse(string, fmt) -> Tuple[bool, Optional[float]]:
    """Parse to pattern in specific manner"""
    try:
        dt = datetime.datetime.strptime(string, fmt)
        return True, int(time.mktime(dt.timetuple()))
    except ValueError:
        return False, None


def _try_parse(timestr: str) -> Optional[float]:
    """Iteratively figure out what pattern suits the situation"""
    for pat in _PATTERNS:
        success, retval = _datetime_parse(timestr, pat)
        if success:
            return retval
    return None


def timespec_valid(string: str) -> int:
    """Validation for time type arguments"""
    string = string.lstrip()
    if string.startswith("-"):
        string = string[1:]
        try:
            value, unit = _TIMESPEC_GENERAL.findall(string)[0]
        except IndexError as e:
            msg = "%r is not a valid datetime specification" % string
            raise argparse.ArgumentTypeError(msg) from e
        return time.time() - int(value) * INTERVALS.get(unit.upper(), 1)

    elif string[0] == "@":
        return int(string[1:])
    elif string == "now":
        return int(time.time())
    else:
        res = _try_parse(string)
        if res:
            return res
        else:
            msg = "%r is not a valid datetime specification" % string
            raise argparse.ArgumentTypeError(msg)


def mac_name_valid(string) -> str:
    """Mac address format validation"""
    if re.match("^(:?[0-9a-f]{2}:){5}[0-9a-f]{2}$", string.lower()):
        return string.lower()
    else:  # probably a name
        return string
