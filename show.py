#!/usr/bin/env python3
import os
import sys
import time
import datetime
import time
import signal
import errno
import re
import json
import subprocess
import argparse
import socket

def print_table(table):
    col_width = [max(len(str(x)) for x in col) for col in zip(*table)]
    for line in table:
        print ("|" + " | ".join("{:{}}".format(str(x), col_width[i])
                                for i, x in enumerate(line)) + "|")

def size_fmt(num):
    for unit in ['','Ki','Mi','Gi']:
        if abs(num) < 1024.0:
            return "%3.0f%sB" % (num, unit)
        num /= 1024.0
    return "%.0f%sB" % (num, 'Ti')

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


def arg_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="Shows data about network traffic on local network.", epilog="Valid datetime specifier formats (for -s/-e options) are:\nABSOLUTE\n\tdd-mm-yyyyThh:mm:ss (eg. 11-11-2017T11:11:11)\n\tdd-mm-yyyy (eg. 11-11-2017)\nRELATIVE\n\t-NUM - number of second before NOW (eg. -604800)\n\t-NUMm - number of minutes before NOW (eg. -10080m)\n\t-NUMh - number of hours before NOW (eg. -168h)\n\t-NUMd - number of days before NOW (eg. -7d)\n\t-NUMw - number of weeks before NOW (eg. -1w)")
    parser.add_argument("-s", "--start",
                        help="Beginning of time window",
                        metavar='DT',
                        type=timespec_valid
                        )
    parser.add_argument("-e", "--end",
                        help="End of time window",
                        metavar='DT',
                        type=timespec_valid
                        )
    parser.add_argument("-m", "--mac",
                        help="Show just records for specified MAC address OR name (multiple such options can be specified)",
                        action='append',
                        metavar='MAC',
                        type=mac_name_valid
                        )
    parser.add_argument("-H", "--hostname",
                        help="Show just records for specified (destination) hostname (multiple such options can be specified)",
                        metavar='N',
                        action='append'
                        )
    parser.add_argument("--no-filter",
                        action='store_true',
                        help="Don't apply filter to output (hides tracking, advertisements and other rubbish)"
                        )
    parser.add_argument("-A", "--aggregate",
                        action='store_true',
                        help="Display aggregate records (instead of timeline)"
                        )
    return parser.parse_args()

#workaround for relative datetime options for -s/-e (begins with -):
# don't consider -[0-9] to be argument - prepend space - this is enough for argparse
for i, arg in enumerate(sys.argv):
  if (arg[0] == '-') and len(arg)>1 and arg[1].isdigit(): sys.argv[i] = ' ' + arg
args=arg_parser()
query={}
if args.start:
    query["start"]=args.start
if args.end:
    query["end"]=args.end
if args.mac:
    query["mac"]=args.mac
if args.hostname:
    query["hostname"]=args.hostname
if args.no_filter:
    query["filter"]=False
if args.aggregate:
    query["aggregate"]=True
query=json.dumps(query)
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    sock.connect("/var/run/pakon-query.sock")
    sock.sendall((query+"\n").encode())
    with sock.makefile() as f:
        response = f.readline().strip()
except:
    print("Can't get data from pakon-handler. Is it running?")
    sys.exit(1)
finally:
    sock.close()

data=json.loads(response)
if not data:
    print("no records to show")
    sys.exit(0)
for i in range(len(data)):
    if data[i][1]==0:
        data[i][1]="<1s"
    else:
        data[i][1]=str(data[i][1])+"s"
    if data[i][3] and len(data[i][3])>40:
        data[i][3]="..."+data[i][3][-40:]
    data[i][6]=size_fmt(data[i][6])
    data[i][7]=size_fmt(data[i][7])
    data[i]=[str(c) for c in data[i]]
data.insert(0,["datetime", "dur", "src MAC", "hostname", "dst port", "proto", "sent", "recvd"])
data.insert(1,["", "", "", "", "", "", "", ""])
if args.aggregate:
    for i in range(len(data)):
        data[i]=data[i][1:]
print_table(data)
