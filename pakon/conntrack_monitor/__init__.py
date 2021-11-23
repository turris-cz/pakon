import logging

logging.basicConfig(filename="/var/log/conntrack_mon.log", level=logging.INFO)

logger = logging.getLogger("conntrackmon")
logger.level = logging.DEBUG
