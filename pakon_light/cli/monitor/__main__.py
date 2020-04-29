#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import errno
import json
import signal

from pakon_light import settings
from pakon_light.job import PakonJob
from pakon_light.models.traffic import Traffic
from pakon_light.utils import MultiReplace, load_replaces, uci_get
from sqlalchemy import desc, select

from .dns_cache import DNSCache
from .handlers import handle_flow, handle_flow_start, handle_http, handle_tls
from .sources import ConntrackScriptSource, UnixSocketSource
from .utils import everyN, get_dev_mac, is_flow_to_delete

# Maximum number of records in the live database - to prevent filling all available space it's recommended not to touch
# this, unless you know really well what you're doing filling all available space in /var/lib (tmpfs) will probably
# break your router.

HARD_LIMIT = 3000000

CHECK_DB_OVERFLOW_EVERY = 100000


def main():
    MonitorJob().run()


class MonitorJob(PakonJob):
    def __init__(self):
        super().__init__(with_live_db=True)
        self.dns_cache = DNSCache()
        self.domain_replace = MultiReplace(load_replaces())
        self.dns_cache.try_load()
        self.data_source = self.get_data_source()
        self.allowed_interfaces = uci_get('pakon.monitor.interface')
        self.hard_limit = int(uci_get('pakon.monitor.database_limit') or HARD_LIMIT)

    @staticmethod
    def get_data_source():
        if uci_get('pakon.monitor.mode').strip() == 'filter':
            return ConntrackScriptSource()
        return UnixSocketSource()

    def main(self, args):
        self.clear_records_with_flow_id()
        self.set_signal_handlers()
        self.run_main_loop()

    def clear_records_with_flow_id(self):
        """
        flow_ids are only unique (and meaningful) during one run of this script flows with flow_id are incomplete,
        delete them.
        """
        settings.logger.info('Clear records with flow_id.')
        deleted_traffic_count = self.live_db_session.query(Traffic).filter(Traffic.flow_id.isnot(None)).delete()
        self.live_db_session.commit()
        settings.logger.info('%s records with flow_id cleared.', deleted_traffic_count)

    def set_signal_handlers(self):
        signal.signal(signal.SIGUSR1, self.reload_replaces)

    def reload_replaces(self):
        settings.logger.info("Reloading domain replaces.")
        self.domain_replace.setup(load_replaces())

    def run_main_loop(self):
        run_check = everyN(CHECK_DB_OVERFLOW_EVERY)

        settings.logger.debug("Start listening...")
        while True:
            try:
                line = self.data_source.get_message()
                if not line:
                    break
                settings.logger.debug(line)

                try:
                    data = json.loads(line)
                except ValueError:
                    settings.logger.warning("Error decoding json.")
                    continue
                if 'ether' not in data or 'src' not in data['ether']:
                    data['ether'] = {}
                    data['ether']['src'] = ''

                if data['event_type'] == 'flow_start' and data['flow']:
                    self.handle_new_traffic(data)
                elif data['event_type'] == 'dns' and data['dns']:
                    self.handle_dns(data)
                else:
                    self.handle_update_traffic(data)

                if run_check:
                    self.check_and_solve_db_overflow()

            except KeyboardInterrupt as e:
                self.dns_cache.dump()
                settings.logger.info('DNS cache dumped.')
                raise e

            except IOError as e:
                if e.errno != errno.EINTR:
                    raise

    def handle_new_traffic(self, data):
        traffic = handle_flow_start(data, self.allowed_interfaces, self.dns_cache, self.domain_replace)
        if traffic:
            self.live_db_session.add(traffic)
            self.live_db_session.commit()

    def handle_dns(self, data):
        is_answer = data['dns']['type'] == 'answer'
        check_rrtype = 'rrtype' in data['dns'].keys() and data['dns']['rrtype'] in ('A', 'AAAA', 'CNAME')

        if is_answer and check_rrtype:
            settings.logging.debug('Saving DNS data')
            dev, mac = get_dev_mac(data['dest_ip'])
            self.dns_cache.set(mac, data['dns']['rrname'], data['dns']['rdata'])

    def handle_update_traffic(self, data):
        traffic_values = None
        flow_id = data['flow_id']
        if data['event_type'] == 'flow' and data['flow']:
            if 'app_proto' not in data or data['app_proto'] == 'failed':
                data['app_proto'] = '?'
            if is_flow_to_delete(data):
                self.live_db_session.query(Traffic).filter(Traffic.flow_id == flow_id).delete()
                return None
            else:
                traffic_values = handle_flow(data)
        elif data['event_type'] == 'tls' and data['tls']:
            traffic_values = handle_tls(data, self.domain_replace)
        elif data['event_type'] == 'http' and data['http']:
            traffic_values = handle_http(data, self.domain_replace)
        else:
            settings.logger.warning("Unknown event type.")

        if traffic_values:
            self.live_db_session.query(Traffic).filter(Traffic.flow_id == flow_id).update(traffic_values)
            self.live_db_session.commit()

    def check_and_solve_db_overflow(self):
        traffic = self.traffic
        hard_limit = self.hard_limit
        count = self.traffic.count()

        if count > self.hard_limit:
            settings.logger.warning('Over %s records in the live database ({}) -> deleting.', hard_limit, count)
            delete_over_limit_query = traffic.delete().where(
                traffic.c.id.in_(
                    select([traffic.c.id]).order_by(desc(traffic.c.id)).limit(-1).offset(hard_limit)
                )
            )
            self.connection.execute(delete_over_limit_query)

    def close_db_connection(self):
        self.connection.close()


if __name__ == "__main__":
    main()
