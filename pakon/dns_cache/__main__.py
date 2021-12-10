import sys
import json
import traceback

from pakon.utils import open_process
from pakon.dns_cache.database import Dns
from pakon.dns_cache.utils import Objson

from pakon.dns_cache import logger

_DNS_MONITOR = ["/usr/bin/tls_dns_dump", "-i", "br-lan"]


def main():
    with open_process(_DNS_MONITOR) as proc:
        try:
            counter = 1
            for line in proc.stdout:
                d, exists = Dns().get_or_create(Objson(json.loads(line)))
                type_ = "ssl" if d.is_ssl else "dns"
                if exists:
                    logger.info(
                        f"skipping >> {type_.upper()}, entry {d.server_ip}, name: {d.name} record exists."
                    )
                else:
                    d.save()
                    logger.info(
                        f"record |> {type_.upper()} entry, src mac/ip:{d.client.mac}, dst_ip: {d.server_ip}, name: {d.name}"
                    )

                if counter >= 126:
                    Dns.retention_apply(5)
                    counter = 0
                counter += 1
        except KeyboardInterrupt:
            sys.exit(0)

        except Exception as e:
            _, _, exc_traceback = sys.exc_info()
            logger.error(
                f"Error: {e}, Traceback: {repr(traceback.extract_tb(exc_traceback))}, line {line}"
            )


if __name__ == "__main__":
    main()
