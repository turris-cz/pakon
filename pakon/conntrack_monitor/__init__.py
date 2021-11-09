from enum import Enum
from os import O_LARGEFILE
import subprocess
import logging
import sys
import traceback

from typing import Tuple, TypeVar

from pakon.utils.xml_flow_parser import Element, Parser
from pakon.utils import open_process

from copy import deepcopy

from peewee import BigIntegerField, DoesNotExist, IntegerField, Model, BlobField, PrimaryKeyField, Select, SqliteDatabase, TextField

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
    id = PrimaryKeyField()
    xml = BlobField()  # debug data, remove in production
    flow_id = BigIntegerField(unique=True)
    proto = TextField()
    src_ip = TextField()
    dest_ip = TextField()
    src_port = IntegerField(null=True)
    dest_port = IntegerField(null=True)
    packets_recvd = IntegerField(default=0)
    bytes_recvd = IntegerField(default=0)
    packets_sent = IntegerField(default=0)
    bytes_sent = IntegerField(default=0)

    @classmethod
    def get_filter_original_or_create(cls, flow: Element, xml: bytes) -> Tuple[FlowType,bool]:
        orig = flow.original
        if orig.layer4.protoname == "icmp":
             return cls.create(
                proto = orig.layer4.protoname,
                src_ip = orig.layer3.src.value,
                dest_ip = orig.layer3.dst.value,
                flow_id = flow.independent.id.value
             ), False
        try:
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


logging.basicConfig(filename="/var/log/conntrack_mon.log", level=logging.INFO)

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
                        logging.info(f'skipping >> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}')
                    elif flow.proto == "icmp":
                        logging.info(f'skipping >> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, flow_id: {flow_id}')
                        pass
                    else:
                        # brand new type of flow, save for later
                        flow.save()
                        logging.info(f'saving |> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, flow_id: {flow.flow_id}')

                else:  # if p.root.flow.type =="destroy":
                    if success:
                       
                        # if we not, just update the counters and transfer the id
                        new_id = p.root.flow.independent.id.value
                        old_id = flow.flow_id
                        # we need to filter whether we select flow with same id
                        if flow.flow_id != new_id:
                            flow.flow_id = new_id
                        flow.packets_recvd += p.root.flow.original.counters.packets.value
                        flow.bytes_recvd += p.root.flow.original.counters.bytes.value
                        flow.packets_sent += p.root.flow.reply.counters.packets.value
                        flow.bytes_sent += p.root.flow.reply.counters.bytes.value
                        logging.info(f'updating + {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, flow_id: {old_id}->{new_id}')
                        flow.save()
                            
                    else:
                        # flow has not existed (we started to capture when the flow already existed)
                        flow.packets_recvd = p.root.flow.original.counters.packets.value
                        flow.bytes_recvd = p.root.flow.original.counters.bytes.value
                        flow.packets_sent = p.root.flow.reply.counters.packets.value
                        flow.bytes_sent = p.root.flow.reply.counters.bytes.value
                        flow.save()
                        logging.info(f'counters ^ {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, flow_id: {flow.flow_id}, id: {flow.id}')


        except KeyboardInterrupt as e:
            logging.info(f'Exited gracefully: 0')
            sys.exit(0)
        
        except Exception as e:
            logging.error(f'error: {e} on line {line}')
            sys.exit(1)
