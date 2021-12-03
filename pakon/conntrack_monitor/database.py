from re import I
from typing import Union, TypeVar, Tuple, List
from datetime import datetime, timedelta
from pakon.dns_cache.database import Dns


from pakon.conntrack_monitor import logger
from logging import DEBUG

from peewee import (
    BigIntegerField,
    DateTimeField,
    DoesNotExist,
    IntegerField,
    Model,
    # BlobField,
    PrimaryKeyField,
    SqliteDatabase,
    TextField,
)

from pakon.utils.xml_flow_parser import Element
from pakon.dns_cache.utils import LeasesCache

db = SqliteDatabase("/var/lib/conntrack_debug.db")

FlowType = TypeVar("FlowType", bound="Flow")


class __BaseModel(Model):
    class Meta:
        database = db


_LEASES_CACHE = LeasesCache()


class Flow(__BaseModel):
    id = PrimaryKeyField()
    # xml = BlobField()  # debug data, remove in production
    flow_id = BigIntegerField()
    proto = TextField()
    src_mac = TextField()
    dest_ip = TextField()
    dest_name = TextField(null=True)
    # src_port = IntegerField(null=True)
    dest_port = IntegerField(null=True)
    packets_recvd = IntegerField(default=0)
    bytes_recvd = IntegerField(default=0)
    packets_sent = IntegerField(default=0)
    bytes_sent = IntegerField(default=0)
    used = DateTimeField(default=datetime.now)

    @staticmethod
    def translate(obj):
        _ip = obj.layer3.src.value
        return _LEASES_CACHE.ip_mapping.get(_ip, {"mac": _ip}).get(
            "mac"
        )  # if not found, return the ip at least

    @classmethod
    def get_filter_original_or_create(
        cls, flow: Element, xml: bytes
    ) -> Tuple[FlowType, bool]:
        orig = flow.original
        src_mac = Flow.translate(orig)
        # get the server saved dns hosntame
        ret = Dns.get_hostname(src_mac, orig.layer3.dst.value)
        name = ret.name if isinstance(ret, Dns) else None
        try:
            return (
                cls.select()
                .where(
                    cls.proto == f"{orig.layer3.protoname}/{orig.layer4.protoname}",
                    cls.src_mac == src_mac,
                    cls.dest_ip == orig.layer3.dst.value,
                    cls.dest_port == orig.layer4.dport.value,
                )
                .get(),
                True,
            )
        except DoesNotExist:
            return (
                cls(
                    xml=xml,
                    proto=f"{orig.layer3.protoname}/{orig.layer4.protoname}",
                    src_mac=src_mac,
                    dest_name=name,
                    dest_ip=orig.layer3.dst.value,
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
        _LEASES_CACHE.update_data()
        if logger.level == DEBUG:
            ret = []
            it = dead_flows.iterator()
            for flow in it:
                ret.append(flow)
                flow.delete_instance()
            return ret
        else:
            count_deleted = dead_flows.delete()
            return count_deleted

    class Meta:
        table_name = "flows"


def create_table():
    db.drop_tables([Flow])
    db.create_tables([Flow])
