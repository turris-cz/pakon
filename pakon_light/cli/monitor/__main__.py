#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import errno
import json
import signal
import sqlite3

from pakon_light import settings
from pakon_light.job import Job
from pakon_light.utils import uci_get

from .dns_cache import DNSCache
from .sources import ConntrackScriptSource, UnixSocketSource
from .utils import (
    MultiReplace,
    everyN,
    exit_gracefully,
    handle_dns,
    handle_flow,
    handle_flow_start,
    handle_http,
    handle_tls,
    load_replaces,
    reload_replaces
)


def main():
    MonitorJob().run()


class MonitorJob(Job):
    def main(self, args):
        dns_cache = DNSCache()
        domain_replace = MultiReplace(load_replaces())
        known_devices = set()

        archive_path = uci_get('pakon.archive.path') or '/srv/pakon/pakon-archive.db'

        dns_cache.try_load()
        # isolation_level=None for autocommit mode - we dont want long-lasting transactions
        con = sqlite3.connect('/var/lib/pakon.db', isolation_level=None)
        # flow_ids are only unique (and meaningful) during one run of this script
        # flows with flow_id are incomplete, delete them
        try:
            con.execute('DELETE FROM traffic WHERE flow_id IS NOT NULL')
        except:
            settings.logger.debug('Error cleaning flow_id')
        notify_new_devices = int(uci_get('pakon.monitor.notify_new_devices'))
        if notify_new_devices:
            con.execute('ATTACH ? AS archive', (archive_path,))
            for row in con.execute(
                    'SELECT DISTINCT(src_mac) FROM traffic UNION SELECT DISTINCT(src_mac) FROM archive.traffic'
            ):
                known_devices.add(row[0])
            con.execute('DETACH archive')

        if uci_get('pakon.monitor.mode').strip() == 'filter':
            data_source = ConntrackScriptSource()
        else:
            data_source = UnixSocketSource()

        signal.signal(signal.SIGINT, exit_gracefully)
        signal.signal(signal.SIGTERM, exit_gracefully)
        signal.signal(signal.SIGUSR1, reload_replaces)

        allowed_interfaces = uci_get('pakon.monitor.interface')

        settings.logger.debug("Listening...")
        # maximum number of records in the live database - to prevent filling all available space
        # it's recommended not to touch this, unless you know really well what you're doing
        # filling all available space in /var/lib (tmpfs) will probably break your router
        hard_limit = int(uci_get('pakon.monitor.database_limit') or 3000000)
        run_check = everyN(100000)

        while True:
            try:
                line = data_source.get_message()
                if not line:
                    break
                settings.logger.debug(line)
                try:
                    data = json.loads(line)
                except ValueError:
                    settings.logger.warning("Error decoding json")
                    continue
                if 'ether' not in data.keys() or 'src' not in data['ether'].keys():
                    data['ether'] = {}
                    data['ether']['src'] = ''
                if data['event_type'] == 'dns' and data['dns']:
                    handle_dns(data, dns_cache)
                elif data['event_type'] == 'flow' and data['flow']:
                    handle_flow(data, con)
                elif data['event_type'] == 'tls' and data['tls']:
                    handle_tls(data, con, domain_replace)
                elif data['event_type'] == 'http' and data['http']:
                    handle_http(data, con, domain_replace)
                elif data['event_type'] == 'flow_start' and data['flow']:
                    handle_flow_start(
                        data,
                        notify_new_devices,
                        con,
                        allowed_interfaces,
                        known_devices,
                        dns_cache,
                        domain_replace
                    )
                else:
                    settings.logger.warning("Unknown event type")

                if run_check:
                    c = con.cursor()
                    c.execute('SELECT COUNT(*) FROM traffic')
                    count = int(c.fetchone()[0])
                    c.close()
                    if count > hard_limit:
                        settings.logger.warning('over {} records in the live database ({}) -> deleting', hard_limit,
                                                 count)
                        con.execute(
                            'DELETE FROM traffic WHERE ROWID IN (SELECT ROWID FROM traffic ORDER BY ROWID DESC LIMIT -1 OFFSET ?)',
                            hard_limit
                        )
            except KeyboardInterrupt:
                exit_gracefully()
            except IOError as e:
                if e.errno != errno.EINTR:
                    raise
            except sqlite3.DatabaseError as e:
                settings.logger.warning("Database error: " + str(e))
            except sqlite3.OperationalError as e:
                settings.logger.warning("Database operational error: " + str(e))


if __name__ == "__main__":
    main()
