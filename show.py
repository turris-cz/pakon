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

if (len(sys.argv)<2):
    print("usage: {} query".format(sys.argv[0]))
    sys.exit(1)
try:
    response=subprocess.check_output(['/usr/bin/python3', '/usr/libexec/pakon-light/dump.py', sys.argv[1]]).decode()
except OSError:
    print("error calling dump.py")
    sys.exit(1)

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

data=json.loads(response)
for i in range(len(data)):
    data[i][0]=datetime.datetime.fromtimestamp(int(data[i][0])).strftime('%Y-%m-%d %H:%M:%S')
    if data[i][1]==0:
        data[i][1]="<1s"
    else:
        data[i][1]=str(data[i][1])+"s"
    if data[i][3] and len(data[i][3])>40:
        data[i][3]="..."+data[i][3][-40:]
    data[i][6]=size_fmt(data[i][6])
    data[i][7]=size_fmt(data[i][7])
    data[i]=[str(c) for c in data[i]]
print_table(data)
