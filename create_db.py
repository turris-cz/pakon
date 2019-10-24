#!/usr/bin/env python3
import os
import sqlite3
import subprocess
from euci import EUci


os.makedirs("/var/lib", exist_ok=True)
con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()
c.execute('CREATE TABLE IF NOT EXISTS traffic (flow_id integer, start real, duration integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)')
c.execute('create table if not exists "alerts" (start real, src_ip text, src_port int, dest_ip text, dest_port int, proto text, app_proto text null, gid int, sid int, rev int, signature text, category text, severity int, bytes_send int, bytes_received int);')
c.execute('CREATE INDEX IF NOT EXISTS start ON traffic(start)')
c.execute('CREATE INDEX IF NOT EXISTS archive1 ON traffic(src_mac, start, COALESCE(app_hostname,dest_ip))')
c.execute('CREATE UNIQUE INDEX IF NOT EXISTS flow_id ON traffic(flow_id) WHERE flow_id IS NOT NULL')
c.execute('PRAGMA user_version=1')
con.commit()
con.close()

with EUci() as uci:
    archive_path = uci.get(
        'pakon', 'archive', 'path',
        dtype=str,
        default='/srv/pakon/pakon-archive.db'
    )

os.makedirs(os.path.dirname(os.path.abspath(archive_path)), exist_ok=True)
con = sqlite3.connect(archive_path)
c = con.cursor()
c.execute('CREATE TABLE IF NOT EXISTS traffic (start real, duration integer, details integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)')
c.execute('create table if not exists "alerts" (start real, duration int, count int, details int, src_ip text, src_port int, dest_ip text, dest_port int, proto text, app_proto text null, gid int, sid int, rev int, signature text, category text, severity int, bytes_send int, bytes_received int);')
c.execute('DROP INDEX IF EXISTS traffic_lookup')
c.execute('CREATE INDEX IF NOT EXISTS archive1 ON traffic(details, src_mac, COALESCE(app_hostname,dest_ip), start)')
c.execute('CREATE INDEX IF NOT EXISTS start ON traffic(start)')
c.execute('CREATE INDEX IF NOT EXISTS dest_port ON traffic(dest_port)')
c.execute('PRAGMA user_version=1')
con.commit()
con.close()
