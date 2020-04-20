#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

from sqlalchemy import Integer, Column, Index, func

from .traffic_base import TrafficBase

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TrafficArchive(Base, TrafficBase):
    details = Column(Integer)
    dest_port = Column(Integer, index=True)

    __table_args__ = (
        Index('archive', 'details', 'src_mac', func.coalesce('app_hostname', 'dest_ip')),
    )

    def __repr__(self):
        return f'<Traffic()>'
