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

def timezone_offset():
    is_dst = time.daylight and time.localtime().tm_isdst > 0
    utc_offset = - (time.altzone if is_dst else time.timezone)
    return utc_offset

data=json.loads(response)
for l in data:
    l[0]=datetime.datetime.fromtimestamp(int(l[0])+timezone_offset()).strftime('%Y-%m-%d %H:%M:%S')
    print(l)
