import sys
import json

from datetime import datetime

from pakon.utils import open_process
from pakon.dns_cache.database import Dns
from pakon.dns_cache.utils import Objson

from pakon.dns_cache import logger

_DNS_MONITOR = ["/usr/bin/tls_dns_dump", "-i", "br-lan"]

def main():
    with open_process(_DNS_MONITOR) as proc:
        try:
            for line in proc.stdout:
                # print(f'Line: {line} {datetime.strftime(datetime.now(), "%h:%m%:s")}')
                d, exists = Dns().get_or_create(Objson(json.loads(line)))
                type_ = "ssl" if d.is_ssl else "dns"
                ssl = f' client_port: {d.client_port}' if d.is_ssl else ''
                if exists:
                    logger.info(f'skipping >> {type_.upper()} entry {d.server_ip} record exists.')
                else:
                    d.save()
                    logger.info(f'record |> {type_.upper()} entry src_ip:{d.client.mac} dst_ip: {d.server_ip} name: {d.name}{ssl}')

        except KeyboardInterrupt:
            sys.exit(0)

        except Exception as e:
            logger.error(f'Error: {e}')


if __name__ == '__main__':
    main()
