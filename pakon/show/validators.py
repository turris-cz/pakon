import argparse
import time
import datetime
import re

def datetime_parse(string, format):
    try:
        dt = datetime.datetime.strptime(string, format)
        return int(time.mktime(dt.timetuple()))
    except ValueError:
        return None

def timespec_valid(string):
    string=string.lstrip()
    if string[0]=='-':
        string=string[1:]
        if not re.match("[0-9]+[WDHMwdhm]?$", string):
            msg = "%r is not a valid datetime specification" % string
            raise argparse.ArgumentTypeError(msg)
        if string[-1].upper()=="W":
            return int(time.time())-int(string[:-1])*86400*7
        elif string[-1].upper()=="D":
            return int(time.time())-int(string[:-1])*86400
        elif string[-1].upper()=="H":
            return int(time.time())-int(string[:-1])*3600
        elif string[-1].upper()=="M":
            return int(time.time())-int(string[:-1])*60
        else:
            return int(time.time())-int(string)
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
    if re.match("[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}$", string.lower()):
        return string.lower()
    else: #probably a name
        return string