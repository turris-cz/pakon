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

def duration_valid(string):
    if not re.match("[0-9]+[WDhm]?$", string):
        msg = "%r is not a valid time specification" % string
        raise argparse.ArgumentTypeError(msg)
    if string[-1]=="W":
        return int(string[:-1])*86400*7
    elif string[-1]=="D":
        return int(string[:-1])*86400
    elif string[-1]=="h":
        return int(string[:-1])*3600
    elif string[-1]=="m":
        return int(string[:-1])*60
    else:
        return int(string)

def mac_valid(string):
    if not re.match("[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}$", string.lower()):
        msg = "%r is not a valid MAC address" % string
        raise argparse.ArgumentTypeError(msg)
    return string.lower()


def arg_parser():
    parser = argparse.ArgumentParser()
    start_spec = parser.add_mutually_exclusive_group()
    start_spec.add_argument("-b", "--before",
                        help="Beginning of time window - relative time",
                        type=duration_valid
                        )
    start_spec.add_argument("-s", "--start",
                        help="Beginning of time window - absolute time",
                        type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d%H:%i:%s')
                        )
    parser.add_argument("-l", "--length",
                        help="Length of time window",
                        type=duration_valid
                        )
    parser.add_argument("-m", "--mac",
                        help="Show just records for specified MAC address (multiple such options can be specified)",
                        action='append',
                        type=mac_valid
                        )
    parser.add_argument("-H", "--hostname",
                        help="Show just records for specified hostname (multiple such options can be specified)",
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
    args=parser.parse_args()
    if args.length and not (args.before or args.start):
        parser.error("--length required either --before of --start to be specified")
        sys.exit(1)
    return args


args=arg_parser()
query={}
if args.before:
    query["start"]=time.time() - args.before
if args.start:
    query["start"]=args.start
if args.length:
    query["end"]=query["start"] + args.length
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
    response = sock.makefile().readline().strip()
except:
    print("Can't get data from pakon-handler. Is it running?")
    sys.exit(1)
finally:
    sock.close()

#print(response)
data=json.loads(response)
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
data.insert(0,["datetime", "dur.", "src MAC", "hostname", "dst port", "proto", "send", "recvd"])
data.insert(1,["", "", "", "", "", "", "", ""])
if args.aggregate:
    for i in range(len(data)):
        data[i]=data[i][1:]
print_table(data)
