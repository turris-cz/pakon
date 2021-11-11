import logging
from re import DEBUG
import sys
from datetime import datetime, time, timedelta

from xmlschema import XMLSchemaValidationError
from typing import List, Tuple, TypeVar, Union

from pakon.utils.xml_flow_parser import Element, Parser
from pakon.utils import open_process
from pakon.utils.validation import validate_xml

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

db = SqliteDatabase("/var/lib/conntrack_debug.db")

_CONNTRACK_WATCH = ["/usr/bin/conntrack-watch", "-se"]

FlowType = TypeVar("FlowType", bound="Flow")

logging.basicConfig(filename="/var/log/conntrack_mon.log", level=logging.INFO)

_logger = logging.getLogger("conntrackmon")


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
        if _logger.level == DEBUG:
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


def _log_flow_action(action: str, flow: Flow, custom_id: str = None, level="info"):
    """Helper function to format log"""
    _logging_action = getattr(_logger, level)
    _id = custom_id if custom_id else f"flow_id: {flow.flow_id}"
    _logging_action(f"[{action}] {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, {_id}")


if __name__ == "__main__":
    with open_process(_CONNTRACK_WATCH) as proc:
        try:
            counter = 0
            for line in proc.stdout:
                try:
                    validate_xml(line)
                    p = Parser()
                    p.parse(line.decode())
                    # current_flow = _current_flow_args(p.root.flow)  DEPRACATED
                    flow, success = Flow.get_filter_original_or_create(
                        p.root.flow, line
                    )  # check for flow in history
                    if (
                        p.root.flow.type == "new"
                    ):  # new flow does not contain any counter data, skip it

                        if success:
                            # skip this flow, alrady exists
                            _log_flow_action(" skipping >> ", flow)
                            # _logger.info(f'skipping >> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, flow_id: {flow.flow_id}')
                        else:
                            # brand new type of flow, save for later
                            _log_flow_action(" saving |> ", flow)
                            # _logger.info(f'saving |> {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, flow_id: {flow.flow_id}')
                            flow.save()

                    else:  # if p.root.flow.type =="destroy":
                        flow.used = datetime.now()
                        if success:
                            log_new = False
                            # if we not, just update the counters and transfer the id
                            new_id = p.root.flow.independent.id.value
                            old_id = flow.flow_id
                            # we need to filter whether we select flow with same id
                            if flow.flow_id != new_id:
                                flow.flow_id = new_id
                                log_new = True
                            flow.packets_recvd += (
                                p.root.flow.original.counters.packets.value
                            )
                            flow.bytes_recvd += (
                                p.root.flow.original.counters.bytes.value
                            )
                            flow.packets_sent += (
                                p.root.flow.reply.counters.packets.value
                            )
                            flow.bytes_sent += p.root.flow.reply.counters.bytes.value
                            _log_flow_action(
                                " updating ^ ",
                                flow,
                                custom_id="flow_id: " + f"{old_id}->{new_id}"
                                if log_new
                                else old_id,
                            )
                            # _logger.info(f'updating + ')

                        else:
                            # flow has not existed (we started to capture when the flow already existed)
                            flow.packets_recvd = (
                                p.root.flow.original.counters.packets.value
                            )
                            flow.bytes_recvd = p.root.flow.original.counters.bytes.value
                            flow.packets_sent = p.root.flow.reply.counters.packets.value
                            flow.bytes_sent = p.root.flow.reply.counters.bytes.value
                            _log_flow_action("counters + ", flow)
                            # _logger.info(f'counters ^ {flow.src_ip} to {flow.dest_ip} @ {flow.proto}, flow_id: {flow.flow_id}')
                        flow.save()
                    if counter >= 100:
                        ret = Flow.retention_apply(5)
                        if isinstance(ret, list):
                            for flow_to_delete in ret:
                                _log_flow_action("dropping v ", flow_to_delete)
                        counter = 0
                    counter += 1

                except XMLSchemaValidationError as e:
                    _logger.info(f"[ ignoring >> ] {line}, Validation error: {e}")

        except KeyboardInterrupt as e:
            _logger.info(f"Exited gracefully: 0")
            sys.exit(0)

        except Exception as e:
            _logger.error(f"error: {e} on line {line}")
            sys.exit(1)
