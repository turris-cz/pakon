from datetime import datetime, timedelta
from typing import TypeVar, Tuple
from dns_cache import _logger

from pakon.dns_cache.utils import Objson, load_leases
from pakon import Config

from peewee import (
    Model,
    BooleanField,
    DoesNotExist,
    ForeignKeyField,
    IntegerField,
    PrimaryKeyField,
    SqliteDatabase,
    TextField,
    DateTimeField,
)
db = SqliteDatabase("/var/lib/dns_cache.db")

ClientType = TypeVar("ClientType", bound="Client")
DnsType = TypeVar("DnsType", bound="Dns")

class __BaseModel(Model):
    used = DateTimeField(default=datetime.now)

    class Meta:
        database = db
    
    @classmethod
    def retention_apply(cls, minutes):
        res = cls.delete().where(
            cls.used < datetime.now() - timedelta(minutes=minutes),
        )
        _logger.info('deleted {res} records from {cls.table}')


class Client(__BaseModel):
    client_id = PrimaryKeyField()
    ip = TextField(unique=True)
    mac = TextField()
    hostname = TextField()

    @classmethod
    def select_or_create(cls, query: str) -> ClientType:
        leases = load_leases()
        mac, hostname = "", ""
        if query in leases.keys():
            lease = leases.get(query)
            mac = lease.get("mac")
            hostname = lease.get("hostname")
        try:
            c = cls.select().where(cls.ip==query).get()
            c.mac = mac
            c.hostname = hostname
            c.used = datetime.now()
            return c
        except DoesNotExist:
            return cls.create(ip=query, mac=mac, hostname=hostname)

    class Meta:
        table_name = 'clients'

class Dns(__BaseModel):
    client = ForeignKeyField(Client, to_field="client_id", backref="dns_records")
    client_port = IntegerField(null=True)
    server_ip = TextField()
    name = TextField()
    is_ssl = BooleanField()

    def get_or_create(cls, entry: Objson) -> Tuple[DnsType,bool]:
        """Returns obect regardles if is in db or not,
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
        client = Client().select_or_create(client_ip)

        try:  # filter out duplicates, different criteria is with ssl and dns
            if is_ssl:
                record = cls.select().where(
                    (cls.client==client) & (cls.client_port==client_port) & (cls.server_ip==server_ip)
                ).get()
            else:
                record = cls.select().where(
                    (cls.client==client) & (cls.server_ip==server_ip)
                ).get()
            return record, True
        except DoesNotExist:
            return cls.create(
                client=client,
                client_port=client_port,
                server_ip=server_ip,
                name=name,
                is_ssl=is_ssl
            ), False


def create_tables():
    db.drop_tables([Client, Dns])
    db.create_tables([Client, Dns])
