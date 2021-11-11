from typing import TypeVar, Tuple

from pakon.utils import Objson

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
db = SqliteDatabase("/var/lib/dns_cache.db")

ClientType = TypeVar("ClientType", bound="Client")
DnsType = TypeVar("DnsType", bound="Dns")

class __BaseModel(Model):

    class Meta:
        database = db


class Client(__BaseModel):
    client_id = PrimaryKeyField()
    ip = TextField(unique=True)

    @classmethod
    def select_or_create(cls, query: str) -> ClientType:
        try:
            return cls.select().where(cls.ip==query).get()
        except DoesNotExist:
            return cls.create(ip=query)

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
