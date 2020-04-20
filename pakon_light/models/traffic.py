#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

from sqlalchemy import Column, Index, Integer, func
from sqlalchemy.ext.declarative import declarative_base

from .traffic_base import TrafficBase

Base = declarative_base()


class Traffic(Base, TrafficBase):
    flow_id = Column(Integer)
    dest_port = Column(Integer)

    __table_args__ = (
        Index('archive', 'src_mac', 'start', func.coalesce('app_hostname', 'dest_ip')),
        Index('flow_id', 'flow_id', unique=True, sqlite_where=flow_id.isnot(None)),
    )

    def __repr__(self):
        return f'<Traffic()>'
