import subprocess
import sys
import json
from logging import Logger

from peewee import IntegrityError, SqliteDatabase, Model, TextField

_logger = Logger(__name__)

from pakon.utils.objson import Objson

db = SqliteDatabase("/var/lib/dns_cache.db")

__DNS_MONITOR = ["/usr/bin/tls_dns_dump", "-i", "br-lan"]

class BaseModel(Model):
    class Meta:
        database = db

class DNS(BaseModel):
    ip = TextField(unique=True)
    alias = TextField()


def open_process():
    return subprocess.Popen(__DNS_MONITOR, stdout=subprocess.PIPE)


if __name__ == '__main__':
    process = subprocess.Popen(__DNS_MONITOR, stdout=subprocess.PIPE)
    try:
        for line in process.stdout:
            o = Objson(json.loads(line))
            print(o)
            if hasattr(o, "ssl"):
                ip = o.ssl.server_ip
                alias = o.ssl.name
            else:
                ip = o.dns.server_ip
                alias = o.dns.name
            d = DNS(ip=ip, alias=alias)
            try:
                d.save()
                _logger.info(f'saved: {ip}: {alias}')
            except IntegrityError:
                _logger.info(f'record {ip}: {alias} skipped, record exists.')

    except KeyboardInterrupt:
        sys.exit(0)
