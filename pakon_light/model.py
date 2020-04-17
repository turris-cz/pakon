#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

from sqlalchemy import Column, Float, Index, Integer, Sequence, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Traffic(Base):
    __tablename__ = 'traffic'

    id = Column(Integer, Sequence('id_seq'), primary_key=True)
    flow_id = Column(Integer)
    start = Column(Float, index=True)
    duration = Column(Integer)
    src_mac = Column(Text)
    src_ip = Column(Text)
    src_port = Column(Integer)
    dest_ip = Column(Text)
    dest_port = Column(Integer)
    proto = Column(Text)
    app_proto = Column(Text)
    bytes_send = Column(Integer)
    bytes_received = Column(Integer)
    app_hostname = Column(Text)

    __table_args__ = (
        Index('archive', 'src_mac', 'start', func.coalesce('app_hostname', 'dest_ip')),
        Index('flow_id', 'flow_id', unique=True, sqlite_where=flow_id.isnot(None)),
    )

    def __repr__(self):
        return f'<Traffic()>'
