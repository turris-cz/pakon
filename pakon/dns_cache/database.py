from datetime import datetime, timedelta
from typing import TypeVar, Tuple

from pakon.dns_cache.utils import LeasesCache, Objson
from pakon.dns_cache import logger

_LEASES_CACHE = LeasesCache()

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
        logger.info(f'deleted {res} records from "{cls._meta.table_name}"')


class Client(__BaseModel):
    client_id = PrimaryKeyField()
    mac = TextField(unique=True)
    ip = TextField(null=True) # debug, delete in future
    hostname = TextField()

    @classmethod
    def select_or_create(cls, query: str) -> ClientType:
        leases = _LEASES_CACHE.ip_mapping
        mac, hostname = query, "-"
        if query in leases.keys():
            lease = leases.get(query)
            mac = lease.get("mac")
            hostname = lease.get("hostname")
        try:
            c = cls.select().where((cls.mac==mac) | (cls.ip==query)).get()
            c.mac = mac
            c.ip = query
            c.hostname = hostname
            c.used = datetime.now()
            return c
        except DoesNotExist:
            return cls.create(mac=mac, hostname=hostname, ip=query)

    @classmethod
    def retention_apply(cls, minutes):
        super().retention_apply(cls, minutes)
        _LEASES_CACHE.update()

    class Meta:
        table_name = 'clients'

class Dns(__BaseModel):
    client = ForeignKeyField(Client, to_field="client_id", backref="dns_records")
    server_ip = TextField()
    name = TextField()
    is_ssl = BooleanField()

    def get_or_create(cls, entry: Objson) -> Tuple[DnsType,bool]:
        """Returns obect regardles if is in db or not,
True if it is already in database, False if it is created.
"""
        is_ssl = False
        if hasattr(entry, "ssl"):
            # handle ssl
            _ssl = entry.ssl
            client_ip = _ssl.client_ip
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
        log = client.save()
        
        try:  # filter out duplicates
            record = cls.select().where(
                (cls.client==client) & (cls.is_ssl==is_ssl) & (cls.server_ip==server_ip)
            ).get()
            return record, True
        except DoesNotExist:
            return cls.create(
                client=client,
                server_ip=server_ip,
                name=name,
                is_ssl=is_ssl
            ), False
    
#     def get_optimal_hostname(src_ip, dest_ip):
#         """In optimal situation, there should be hostname for only one client. As fallback
# we should return anything we have."""

        

def create_tables():
    db.drop_tables([Client, Dns])
    db.create_tables([Client, Dns])
