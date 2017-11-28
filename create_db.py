#!/usr/bin/env python3

import os
import sqlite3

os.makedirs("/var/lib", exist_ok=True)
con = sqlite3.connect('/var/lib/pakon.db')
c = con.cursor()
c.execute('CREATE TABLE IF NOT EXISTS traffic (flow_id integer, start real, duration integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)')
c.execute('CREATE INDEX IF NOT EXISTS start ON traffic(start)')
c.execute('CREATE UNIQUE INDEX IF NOT EXISTS flow_id ON traffic(flow_id) WHERE flow_id IS NOT NULL')
c.execute('CREATE TABLE IF NOT EXISTS dns (time integer, client text, name text, type text, data text)')
c.execute('CREATE INDEX IF NOT EXISTS tdc ON dns(time,data,client)')
c.execute('PRAGMA user_version=1')
con.commit()
con.close()

os.makedirs("/srv/pakon", exist_ok=True)
con = sqlite3.connect('/srv/pakon/pakon-archive.db')
c = con.cursor()
c.execute('CREATE TABLE IF NOT EXISTS traffic (start real, duration integer, details integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)')
c.execute('CREATE INDEX IF NOT EXISTS traffic_lookup ON traffic(details, start, src_mac)')
c.execute('PRAGMA user_version=1')
con.commit()
con.close()
