import os
import sqlite3

from pakon_light.utils import uci_get


def main():
    os.makedirs("/var/lib", exist_ok=True)
    con = sqlite3.connect('/var/lib/pakon.db')
    c = con.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS traffic (flow_id integer, start real, duration integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)')
    c.execute('CREATE INDEX IF NOT EXISTS start ON traffic(start)')
    c.execute('CREATE INDEX IF NOT EXISTS archive1 ON traffic(src_mac, start, COALESCE(app_hostname,dest_ip))')
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS flow_id ON traffic(flow_id) WHERE flow_id IS NOT NULL')
    c.execute('PRAGMA user_version=1')
    con.commit()
    con.close()

    archive_path = uci_get('pakon.archive.path') or '/srv/pakon/pakon-archive.db'
    os.makedirs(os.path.dirname(os.path.abspath(archive_path)), exist_ok=True)
    con = sqlite3.connect(archive_path)
    c = con.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS traffic (start real, duration integer, details integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)')
    c.execute('DROP INDEX IF EXISTS traffic_lookup')
    c.execute('CREATE INDEX IF NOT EXISTS archive1 ON traffic(details, src_mac, COALESCE(app_hostname,dest_ip), start)')
    c.execute('CREATE INDEX IF NOT EXISTS start ON traffic(start)')
    c.execute('CREATE INDEX IF NOT EXISTS dest_port ON traffic(dest_port)')
    c.execute('PRAGMA user_version=1')
    con.commit()
    con.close()


if __name__ == '__main__':
    main()
