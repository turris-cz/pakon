import subprocess
import logging
import sys

from pakon.utils.xml_flow_parser import Parser
from pakon.utils import open_process

from peewee import Model, BlobField, SqliteDatabase

db = SqliteDatabase("/var/lib/conntrack_debug.db")

_CONNTRACK_WATCH = ["/usr/bin/conntrack-watch","-e"]


class __BaseModel(Model):
    class Meta:
        database = db


class Flow(__BaseModel):
    xml = BlobField()
    json = BlobField()


def create_table():
    db.create_tables([Flow])


logging.basicConfig(filename="/var/log/conntrack_mon.log", level=logging.INFO)


if __name__ == "__main__":
    with open_process(_CONNTRACK_WATCH) as proc:
        try:
            for line in proc.stdout:
                p = Parser()
                p.parse(line.decode())
                json = p.jsonify()
                f = Flow(xml=line,json=json)
                id = f.save()
                logging.info(f'saving: id: {id}')

        except KeyboardInterrupt:
            sys.exit(0)
