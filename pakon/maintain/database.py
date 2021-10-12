import os
import lzma
import sqlite3

from ..utils import uci_get


def databases_integrity_check():
    archive_path = uci_get(
        "pakon.archive.path", default="/srv/pakon/pakon-archive.db"
    )

    compressed_db_path = "/var/lib/pakon.db.xz"
    live_db_path = "/var/lib/pakon.db"

    os.makedirs("/var/lib", exist_ok=True)

    if not os.path.isfile(compressed_db_path):
        return False

    # create live database from compressed one
    # TODO: handle decompression failure
    with lzma.open(compressed_db_path, "rb") as compressed:
        with open(live_db_path, "wb") as uncompressed:
            uncompressed.write(compressed.read())

    # check database file size first
    if os.stat(live_db_path).st_size == 0:
        os.unlink(live_db_path)
        return False

    # check integrity
    con = sqlite3.connect(live_db_path)
    c = con.cursor()
    c.execute("pragma integrity check")
    res = c.fetchone()
    con.close()

    if res[0] != "ok":
        os.unlink(live_db_path)
        return False

    if not os.path.isfile(archive_path):
        return False

    return True


def create_databases():
    os.makedirs("/var/lib", exist_ok=True)
    con = sqlite3.connect("/var/lib/pakon.db")
    c = con.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS traffic (flow_id integer, start real, duration integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)"
    )
    c.execute("CREATE INDEX IF NOT EXISTS start ON traffic(start)")
    c.execute(
        "CREATE INDEX IF NOT EXISTS archive1 ON traffic(src_mac, start, COALESCE(app_hostname,dest_ip))"
    )
    c.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS flow_id ON traffic(flow_id) WHERE flow_id IS NOT NULL"
    )
    c.execute("PRAGMA user_version=1")
    con.commit()
    con.close()

    archive_path = uci_get("pakon.archive.path", default="/srv/pakon/pakon-archive.db")

    os.makedirs(os.path.dirname(os.path.abspath(archive_path)), exist_ok=True)
    con = sqlite3.connect(archive_path)
    c = con.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS traffic (start real, duration integer, details integer, src_mac text, src_ip text, src_port integer, dest_ip text, dest_port integer, proto text, app_proto text, bytes_send integer, bytes_received integer, app_hostname text)"
    )
    c.execute("DROP INDEX IF EXISTS traffic_lookup")
    c.execute(
        "CREATE INDEX IF NOT EXISTS archive1 ON traffic(details, src_mac, COALESCE(app_hostname,dest_ip), start)"
    )
    c.execute("CREATE INDEX IF NOT EXISTS start ON traffic(start)")
    c.execute("CREATE INDEX IF NOT EXISTS dest_port ON traffic(dest_port)")
    c.execute("PRAGMA user_version=1")
    con.commit()
    con.close()
