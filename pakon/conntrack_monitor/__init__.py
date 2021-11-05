from enum import Enum
import subprocess
import logging
import sys
from typing import Tuple, TypeVar

from pakon.utils.xml_flow_parser import Element, Parser
from pakon.utils import open_process

from copy import deepcopy

from peewee import BigIntegerField, DoesNotExist, IntegerField, Model, BlobField, Select, SqliteDatabase, TextField

db = SqliteDatabase("/var/lib/conntrack_debug.db")

_CONNTRACK_WATCH = ["/usr/bin/conntrack-watch","-se"]

FlowType = TypeVar('FlowType', bound='Flow')

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
    flow_id = BigIntegerField(unique=True)
    proto = TextField()
    src_ip = TextField()
    dest_ip = TextField()
    src_port = IntegerField()
    dest_port = IntegerField()
    packets_recvd = IntegerField(null=True)
    bytes_recvd = IntegerField(null=True)
    packets_sent = IntegerField(null=True)
    bytes_sent = IntegerField(null=True)

    @classmethod
    def get_filter_original_or_create(cls, flow: Element, xml: bytes) -> Tuple[FlowType,bool]:
        orig = flow.original
        try:
            logging.debug(orig.dump())
            return cls.select().where(
                cls.proto == f"{orig.layer3.protoname}/{orig.layer4.protoname}",
                cls.src_ip == orig.layer3.src.value,
                cls.dest_ip == orig.layer3.dst.value,
                cls.src_port == orig.layer4.sport.value,
                cls.dest_port == orig.layer4.dport.value
            ).get(), True
        except DoesNotExist:
            return cls.create(
                xml = xml,
                proto = f"{orig.layer3.protoname}/{orig.layer4.protoname}",
                src_ip = orig.layer3.src.value,
                dest_ip = orig.layer3.dst.value,
                src_port = orig.layer4.sport.value,
                dest_port = orig.layer4.dport.value,
                flow_id = flow.independent.id.value
            ), False

    class Meta:
        table_name = 'flows'


def create_table():
    db.drop_tables([Flow])
    db.create_tables([Flow])


logging.basicConfig(filename="/var/log/conntrack_mon.log", level=logging.DEBUG)


def _current_flow_args(flow: Element):
    """Please provide Element.name=="flow"."""

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
                # current_flow = _current_flow_args(p.root.flow)  DEPRACATED
                flow, success = Flow.get_filter_original_or_create(p.root.flow, line)  # check for flow in history
                if p.root.flow.type == "new":  # new flow does not contain any counter data, skip it
                    
                    if success:
                        #skip this flow, alrady exists
                        logging.debug(f'skipping >> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}')
                    else:
                        # brand new type of flow, save for later
                        flow.save()
                        logging.debug(f'saving |> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, id: {flow.flow_id}')

                else:  # if p.root.flow.type =="destroy":
                    if success:
                        # we need to filter whether we select flow with same id
                        # if we not, just update the counters and transfer the id
                        new_id = p.root.flow.independent.id.value
                        if flow.flow_id != new_id:
                            old_id = flow.flow_id
                            flow.flow_id = new_id
                            flow.packets_recvd += p.root.flow.original.counters.packets.value
                            flow.bytes_recvd += p.root.flow.original.counters.bytes.value
                            flow.packets_sent += p.root.flow.reply.counters.packets.value
                            flow.bytes_sent += p.root.flow.reply.counters.bytes.value
                            flow.replace()
                            logging.debug(f'updating |> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, id: {old_id}->{new_id}')
                            break

                    # flow has not existed (we started to capture when the flow already existed)
                    # flow was succesfully selected (flow was started, but counters are not set)
                    flow.packets_recvd = p.root.flow.original.counters.packets.value
                    flow.bytes_recvd = p.root.flow.original.counters.bytes.value
                    flow.packets_sent = p.root.flow.reply.counters.packets.value
                    flow.bytes_sent = p.root.flow.reply.counters.bytes.value
                    flow.replace()
                    logging.debug(f'counters |> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, id: {flow.flow_id}')


        except KeyboardInterrupt:
            sys.exit(0)