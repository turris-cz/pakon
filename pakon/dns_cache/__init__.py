import logging

logging.basicConfig(filename="/var/log/dns_cache.log", level=logging.INFO)

logger = logging.getLogger("dnscache")
