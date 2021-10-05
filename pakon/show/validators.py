import argparse
import time
import datetime
import re

from ..utils import INTERVALS



# split value and unit
# regex.findall(string) -> [(<value>, <unit>)]
_TIMESPEC_GENERAL = re.compile(r"^([0-9]+)([WDHMwdhm]?)$")
_DATETIME = re.compile()

def datetime_parse(string, format):
    try:
        dt = datetime.datetime.strptime(string, format)
        return int(time.mktime(dt.timetuple()))
    except ValueError:
        return None

def timespec_valid(string):
    string = string.lstrip()
    if string.startswith('-'):
        string = string[1:]
        try:
            value, unit = _TIMESPEC_GENERAL.findall(string)[0]
        except IndexError as e:
            msg = "%r is not a valid datetime specification" % string
            raise argparse.ArgumentTypeError(msg) from e
        return time.time() - int(value) * INTERVALS.get(unit.upper(), 1)

    elif string[0]=='@':
        return int(string[1:])
    elif string=='now':
        return int(time.time())
    else:
        if datetime_parse(string, '%d-%m-%YT%H:%M:%S'):
            return datetime_parse(string, '%d-%m-%YT%H:%M:%S')
        if datetime_parse(string, '%d-%m-%Y'):
            return datetime_parse(string, '%d-%m-%Y')
        else:
            msg = "%r is not a valid datetime specification" % string
            raise argparse.ArgumentTypeError(msg)

def mac_name_valid(string):
    if re.match("^(:?[0-9a-f]{2}:){5}[0-9a-f]{2}$", string.lower()):
        return string.lower()
    else: #probably a name
        return string