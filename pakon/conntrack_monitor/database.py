
import logging
from typing import Union, TypeVar, Tuple, List
from datetime import datetime, timedelta

from peewee import (
    BigIntegerField,
    DateTimeField,
    DoesNotExist,
    IntegerField,
    Model,
    BlobField,
    PrimaryKeyField,
    SqliteDatabase,
    TextField,
)

from pakon.utils.xml_flow_parser import Element

db = SqliteDatabase("/var/lib/conntrack_debug.db")

FlowType = TypeVar("FlowType", bound="Flow")

class __BaseModel(Model):
    class Meta:
        database = db


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
    used = DateTimeField(default=datetime.now)

    @classmethod
    def get_filter_original_or_create(
        cls, flow: Element, xml: bytes
    ) -> Tuple[FlowType, bool]:
        orig = flow.original
        # used to filter icmp here, but that is filtered on validation
        try:
            return (
                cls.select()
                .where(
                    cls.proto == f"{orig.layer3.protoname}/{orig.layer4.protoname}",
                    cls.src_ip == orig.layer3.src.value,
                    cls.dest_ip == orig.layer3.dst.value,
                    cls.src_port == orig.layer4.sport.value,
                    cls.dest_port == orig.layer4.dport.value,
                )
                .get(),
                True,
            )
        except DoesNotExist:
            return (
                cls.create(
                    xml=xml,
                    proto=f"{orig.layer3.protoname}/{orig.layer4.protoname}",
                    src_ip=orig.layer3.src.value,
                    dest_ip=orig.layer3.dst.value,
                    src_port=orig.layer4.sport.value,
                    dest_port=orig.layer4.dport.value,
                    flow_id=flow.independent.id.value,
                ),
                False,
            )

    @classmethod
    def retention_apply(cls: FlowType, minutes: int = 10) -> Union[int, List]:
        """Delete records older than n minutes having no flow."""
        dead_flows = cls.select().where(
            cls.used < datetime.now() - timedelta(minutes=minutes),
            cls.bytes_sent == 0,
            cls.bytes_recvd == 0,
        )
        ret = []
        if logging.level == logging.DEBUG:
            it = dead_flows.iterator()
            for flow in it:
                ret.append(flow)
        count_deleted = Flow.delete().where(Flow.in_(dead_flows))
        return ret if ret else count_deleted

    class Meta:
        table_name = "flows"


def create_table():
    db.drop_tables([Flow])
    db.create_tables([Flow])
