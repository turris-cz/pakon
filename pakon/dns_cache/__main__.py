import sys
import json
import gzip

from datetime import datetime

from pakon.utils import open_process
# from pakon.dns_cache.database import Dns
from pakon.dns_cache.utils import Objson

from pakon.dns_cache import logger

_DNS_MONITOR = ["/usr/bin/tls_dns_dump", "-i", "br-lan"]
_DNS_DUMP_PATH = "/srv/pakon/dns_cache.json.gz"


def _unwrap_json(json_):
    """Flatten collected item"""
    data_ = json.loads(json_)
    type = list(data_.keys())[0]
    ret = {**data_[type], "type": type}
    return ret


class DnsEntry:
    def __init__(self, dict):
        self.__dict__ = dict
        if self.type == "ssl":
            del self.__dict__["client_port"]  # we only want to query server port in future
    
    def __eq__(self, __o: object) -> bool:  # enables to compare object to other in order to filter
        return self.__dict__ == __o.__dict__

    def __repr__(self) -> str:
        return f'<DnsEntry {self.type} ip: {self.client_ip}>'
    
    def dump(self):
        return self.__dict__
    


class DnsCache:
    """Process only if certain ammount of data is in stack, watch for duplicate data."""
    def __init__(self, maxlen=64):
        self.stack = []
        self.maxlen = maxlen
    
    def append(self, line):
        entry = DnsEntry(_unwrap_json(line))
        if entry in self.stack:
            logger.info(f'skipping >> {entry.__dict__}')
        else:
            logger.info(f'saving |> {entry.__dict__}')
            self.stack.insert(0, entry)

        if len(self.stack) == self.maxlen:
            logger.info(f'dropping v {self.stack.pop().__dict__}')

    def load():
        try:
            with gzip.open(_DNS_DUMP_PATH, "r"):
                

    def dump():
        pass
    


def main():
    DNS_CACHE = DnsCache()
    DNS_CACHE.load()
    with open_process(_DNS_MONITOR) as proc:
        try:
            for line in proc.stdout:
                # print(f'Line: {line} {datetime.strftime(datetime.now(), "%h:%m%:s")}')
                DNS_CACHE.append(line.decode())
                # d, exists = Dns().get_or_create(Objson(json.loads(line)))
                # type_ = "ssl" if d.is_ssl else "dns"
                # ssl = f' client_port: {d.client_port}' if d.is_ssl else ''
                # if exists:
                #     logger.info(f'skipping >> {type_.upper()} entry {d.server_ip} record exists.')
                # else:
                #     d.save()
                #     logger.info(f'record |> {type_.upper()} entry src_ip:{d.client.mac} dst_ip: {d.server_ip} name: {d.name}{ssl}')

        except KeyboardInterrupt:
            sys.exit(0)

        except Exception as e:
            logger.error(f'Error: {e}')


if __name__ == '__main__':
    main()
