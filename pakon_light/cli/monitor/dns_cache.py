#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import gzip
import json
import os
from collections import OrderedDict

from cachetools import TTLCache, LRUCache


class DNSCache:
    """
    DNS cache internally uses 2 types of cache.
    One (fast_cache)is smaller, with short TTL and there can be a lot of garbage - NS servers A/AAAA, CNAMEs
    The second one (used_cache) is LRU and there are just records that were used at least once - might be used again
    """
    __DB_DUMP_PATH__ = "/srv/pakon/dns_cache.json.gz"

    def __init__(self):
        self.fast_cache = TTLCache(maxsize=1000, ttl=3600)
        self.used_cache = LRUCache(maxsize=2000)

    def dump(self):
        """dump used_cache to __DB_DUMP_PATH__ - so it can survive restart"""
        cache = OrderedDict()
        for item in self.__popitem():
            cache[item[0]] = item[1]
        try:
            with gzip.open(DNSCache.__DB_DUMP_PATH__, 'wb') as f:
                f.write(json.dumps(cache).encode('utf-8'))
        except IOError:
            pass

    def try_load(self):
        """try restoring used_cache from __DB_DUMP_PATH__ - do nothing if it doesn't exist"""
        if os.path.isfile(DNSCache.__DB_DUMP_PATH__):
            try:
                cache = {}
                with gzip.open(DNSCache.__DB_DUMP_PATH__, 'rb') as f:
                    cache = json.loads(f.read().decode('utf-8'), object_pairs_hook=OrderedDict)
                for k, v in cache.items():
                    self.used_cache[k] = v
            except (ValueError, IOError):
                pass

    def __popitem(self):
        while self.used_cache:
            yield self.used_cache.popitem()

    def set(self, src_mac, question, answer):
        """called by handle_dns, adds record to fast_cache"""
        self.fast_cache[src_mac + ":" + answer] = question

    def get(self, src_mac, dest_ip):
        """get name for IP address
        Try used_cache first, if it's not there, try fast_cache
        In fast_cache are also CNAMEs, so it might follow CNAMEs to get the user-requested name.
        If record is found in fast_cache, it's added to used_cache then.
        """
        used = self.used_cache.get(src_mac + ":" + dest_ip)
        if used:
            return used
        name = None
        while True:
            name_ = self.fast_cache.get(src_mac + ":" + (name or dest_ip))
            if not name_:
                if name:
                    self.used_cache[src_mac + ":" + dest_ip] = name
                return name
            name = name_
