import logging
import sys
from datetime import datetime

from xmlschema import XMLSchemaValidationError

from pakon.utils.xml_flow_parser import Parser
from pakon.utils import open_process
from pakon.utils.validation import validate_xml

from pakon.conntrack_monitor.database import Flow



_CONNTRACK_WATCH = ["/usr/bin/conntrack-watch", "-se"]

logging.basicConfig(filename="/var/log/conntrack_mon.log", level=logging.INFO)

_logger = logging.getLogger("conntrackmon")


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
                                _log_flow_action("dropping v ", flow_to_delete, level="debug")
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
