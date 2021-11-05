import subprocess
import logging
import sys

from pakon.utils.xml_flow_parser import Parser
from pakon.utils import open_process

from copy import deepcopy

from peewee import BigIntegerField, DoesNotExist, IntegerField, Model, BlobField, Select, SqliteDatabase, TextField

db = SqliteDatabase("/var/lib/conntrack_debug.db")

_CONNTRACK_WATCH = ["/usr/bin/conntrack-watch","-se"]


class __BaseModel(Model):
    class Meta:
        database = db

# class Flow(__BaseModel):
#     xml = BlobField()
#     json = BlobField()

#     class Meta:
#         table_name = 'flows'

class Flow(__BaseModel):
    xml = BlobField()  # debug data, remove in production
    id = BigIntegerField(unique=True)
    proto = TextField()
    src_ip = TextField()
    dest_ip = TextField()
    src_port = IntegerField()
    dest_port = IntegerField()
    packets_recvd = IntegerField(null=True)
    bytes_recvd = IntegerField(null=True)
    packets_sent = IntegerField(null=True)
    bytes_sent = IntegerField(null=True)

    class Meta:
        table_name = 'flows'


def create_table():
    db.drop_tables([Flow])
    db.create_tables([Flow])


logging.basicConfig(filename="/var/log/conntrack_mon.log", level=logging.INFO)

def _current_flow_args(flow):
    orig = flow.original
    return {
        "proto": f"{orig.layer3.protoname}/{orig.layer4.protoname}",
        "src_ip": orig.layer3.src.value,
        "dest_ip": orig.layer3.dst.value,
        "src_port": orig.layer4.sport.value,
        "dest_port": orig.layer4.dport.value
        }

if __name__ == "__main__":
    with open_process(_CONNTRACK_WATCH) as proc:
        try:
            for line in proc.stdout:
                p = Parser()
                p.parse(line.decode())
                current_flow = _current_flow_args(p.root.flow)
                if p.root.flow.type == "new":
                    query = Flow(**current_flow)
                    try:
                        query.select.get()
                        # skip this flow
                        pass
                    except DoesNotExist:
                        # save the new flow
                        query.id = p.root.flow.independent.id.value
                        query.save()
                else:  # if p.root.flow.type =="destroy":
                    query = Flow(**current_flow)
                    # we need to filter whether we select flow with same id
                    query.select.get()
                    if query.id == p.root.flow.independent.id.value:
                        query.packets_recvd = p.root.flow.original.counters.packets.value
                        query.bytes_recvd = p.root.flow.original.counters.bytes.value
                        query.packets_sent = p.root.flow.reply.counters.packets.value
                        query.bytes_sent = p.root.flow.reply.counters.bytes.value
                        query.save()
                    else:
                        query.id = p.root.flow.independent.id.value
                        query.packets_recvd += p.root.flow.original.counters.packets.value
                        query.bytes_recvd += p.root.flow.original.counters.bytes.value
                        query.packets_sent += p.root.flow.reply.counters.packets.value
                        query.bytes_sent += p.root.flow.reply.counters.bytes.value
                        query.upsert()
                # try:
                #     id = f.save()
                #     logging.info(f'saving: id: {id}')
                # except Exception as e:
                #     logging.error(f'Error: {e}')

        except KeyboardInterrupt:
            sys.exit(0)