#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

from sqlalchemy import Column, Float, Integer, Sequence, Text


class TrafficBase():
    __tablename__ = 'traffic'

    id = Column(Integer, Sequence('id_seq'), primary_key=True)
    start = Column(Float, index=True)
    duration = Column(Integer)
    src_mac = Column(Text)
    src_ip = Column(Text)
    src_port = Column(Integer)
    dest_ip = Column(Text)
    proto = Column(Text)
    app_proto = Column(Text)
    bytes_send = Column(Integer)
    bytes_received = Column(Integer)
    app_hostname = Column(Text)
