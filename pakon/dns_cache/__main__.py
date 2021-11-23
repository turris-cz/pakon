import logging
import sys
import json
from logging import INFO, getLogger


logging.basicConfig(filename="/var/log/dns_cache.log", level=INFO)

_logger = getLogger("dnscache")

from pakon.utils import open_process
from pakon.dns_cache.utils import Objson
from pakon.dns_cache.database import Dns


_DNS_MONITOR = ["/usr/bin/tls_dns_dump", "-i", "br-lan"]


def main():
    with open_process(_DNS_MONITOR) as proc:
        try:
            for line in proc.stdout:
                d, exists = Dns().get_or_create(Objson(json.loads(line)))
                type_ = "ssl" if d.is_ssl else "dns"
                ssl = f' client_port: {d.client_port}' if d.is_ssl else ''
                if exists:
                    _logger.info(f'skipping >> {type_.upper()} entry {d.server_ip} record exists.')
                else:
                    d.save()
                    _logger.info(f'record |> {type_.upper()} entry {d.server_ip}: {d.name}{ssl}')
                   

        except KeyboardInterrupt:
            sys.exit(0)

        except Exception as e:
            _logger.error(f'Error: {e}')


if __name__ == '__main__':
    main()
