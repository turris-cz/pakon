#!/usr/bin/env python3

import os
import sqlite3
import subprocess

#TODO: replace with uci bindings - once available
def uci_get(opt):
    delimiter = '__uci__delimiter__'
    chld = subprocess.Popen(['/sbin/uci', '-d', delimiter, '-q', 'get', opt],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = chld.communicate()
    out = out.strip().decode('ascii','ignore')
    if out.find(delimiter) != -1:
        return out.split(delimiter)
    else:
        return out

os.makedirs("/var/lib", exist_ok=True)
con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()
c.execute('CREATE TABLE IF NOT EXISTS traffic (flow_id integer, start real, duration integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)')
c.execute('CREATE INDEX IF NOT EXISTS start ON traffic(start)')
c.execute('CREATE UNIQUE INDEX IF NOT EXISTS flow_id ON traffic(flow_id) WHERE flow_id IS NOT NULL')
c.execute('PRAGMA user_version=1')
con.commit()
con.close()

archive_path = uci_get('pakon.common.archive_path') or '/srv/pakon/pakon-archive.db'
os.makedirs(os.path.dirname(os.path.abspath(archive_path)), exist_ok=True)
con = sqlite3.connect(archive_path)
c = con.cursor()
c.execute('CREATE TABLE IF NOT EXISTS traffic (start real, duration integer, details integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)')
c.execute('CREATE INDEX IF NOT EXISTS traffic_lookup ON traffic(details, start, src_mac)')
c.execute('PRAGMA user_version=1')
con.commit()
con.close()
