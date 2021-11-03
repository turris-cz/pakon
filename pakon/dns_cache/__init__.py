import logging
from re import L
import sys
import json
from logging import INFO, Logger

from typing import Tuple

from peewee import (
    Model,
    BooleanField,
    DoesNotExist,
    ForeignKeyField,
    IntegerField,
    PrimaryKeyField,
    SqliteDatabase,
    TextField,
)

logging.basicConfig(filename="/var/log/dns_cache.log", level=INFO)

_logger  = Logger(__name__)

from pakon.utils import Objson, open_process

db = SqliteDatabase("/var/lib/dns_cache.db")

_DNS_MONITOR = ["/usr/bin/tls_dns_dump", "-i", "br-lan"]


class __BaseModel(Model):

    class Meta:
        database = db


class Client(__BaseModel):
    client_id = PrimaryKeyField()
    ip = TextField(unique=True)


    class Meta:
        table_name = 'clients'

class DNS(__BaseModel):
    client = ForeignKeyField(Client, to_field="client_id", backref="dns_records")
    client_port = IntegerField(null=True)
    server_ip = TextField()
    name = TextField()
    is_ssl = BooleanField()


def _select_or_create(cls: Client, query: str):
    try:
        return cls.select().where(cls.ip==query).get()
    except DoesNotExist:
        return cls.create(ip=query)


def create_tables():
    db.drop_tables([Client, DNS])
    db.create_tables([Client, DNS])

def _dns_entry(entry: Objson) -> Tuple[DNS,bool]:
    """Returns obect regardles boolena,
True if it is arady in database, False if it is created.
"""
    client_port = None
    is_ssl = False
    if hasattr(entry, "ssl"):
        # handle ssl
        _ssl = entry.ssl
        client_ip = _ssl.client_ip
        client_port = _ssl.client_port
        server_ip = _ssl.server_ip
        name = _ssl.name
        is_ssl = True
    else:
        #handle dns
        _dns = entry.dns
        client_ip = _dns.client_ip
        server_ip = _dns.server_ip
        name = _dns.name
    client = _select_or_create(Client, client_ip)

    try:  # filter out duplicates, different criteria is with ssl and dns
        if is_ssl:
            record = DNS.select().where(
                (DNS.client==client) & (DNS.client_port==client_port) & (DNS.server_ip==server_ip)
            ).get()
        else:
            record = DNS.select().where(
                (DNS.client==client) & (DNS.server_ip==server_ip)
            ).get()
        return record, True
    except DoesNotExist:
        return DNS(
            client=client,
            client_port=client_port,
            server_ip=server_ip,
            name=name,
            is_ssl=is_ssl
        ), False



if __name__ == '__main__':
    with open_process(_DNS_MONITOR) as proc:
        try:
            for line in proc.stdout:
                d, exists = _dns_entry(Objson(json.loads(line)))
                type_ = "ssl" if d.is_ssl else "dns"
                ssl = f' client_port: {d.client_port}' if d.is_ssl else ''
                if exists:
                    _logger.info(f'skipping >> {type_.upper()} entry {d.server_ip} record exists.')
                else:
                    d.save()
                    _logger.info(f'record |> {type_.upper()} entry {d.server_ip}: {d.name}{ssl}')
                   

        except KeyboardInterrupt:
            sys.exit(0)
