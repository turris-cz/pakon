#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

import errno
import json
import signal

from sqlalchemy import MetaData, create_engine, desc, select
from sqlalchemy.exc import ObjectNotExecutableError

from pakon_light import settings
from pakon_light.job import Job
from pakon_light.settings import DB_PATH
from pakon_light.utils import uci_get

from .dns_cache import DNSCache
from .handlers import handle_dns, handle_flow, handle_flow_start, handle_http, handle_tls
from .sources import ConntrackScriptSource, UnixSocketSource
from .utils import MultiReplace, everyN, load_replaces

# Maximum number of records in the live database - to prevent filling all available space
# it's recommended not to touch this, unless you know really well what you're doing
# filling all available space in /var/lib (tmpfs) will probably break your router.
HARD_LIMIT = 3000000

CHECK_DB_OVERFLOW_EVERY = 100000


def main():
    MonitorJob().run()


class MonitorJob(Job):
    def __init__(self):
        self.dns_cache = DNSCache()
        self.domain_replace = MultiReplace(load_replaces())
        self.dns_cache.try_load()
        self.setup_db()
        self.connection, self.traffic = self.setup_db()
        self.data_source = self.get_data_source()
        self.allowed_interfaces = uci_get('pakon.monitor.interface')
        self.hard_limit = int(uci_get('pakon.monitor.database_limit') or HARD_LIMIT)

    @staticmethod
    def setup_db():
        db_engine = create_engine(f'sqlite:///{DB_PATH}', echo=True)
        connection = db_engine.connect()

        meta = MetaData(db_engine)
        meta.reflect(bind=db_engine)
        traffic = meta.tables['traffic']

        return connection, traffic

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
        flow_ids are only unique (and meaningful) during one run of this script
        flows with flow_id are incomplete, delete them.
        """
        traffic = self.traffic
        connection = self.connection

        settings.logger.info('Clear records with flow_id.')
        delete_empty_flow_id = traffic.delete().where(traffic.c.flow_id.isnot(None))
        connection.execute(delete_empty_flow_id)
        settings.logger.info('Records with flow_id cleared.')

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
                if 'ether' not in data.keys() or 'src' not in data['ether'].keys():
                    data['ether'] = {}
                    data['ether']['src'] = ''

                operation = self.handle_data(data)
                try:
                    self.connection.execute(operation)
                except ObjectNotExecutableError:
                    pass

                if run_check:
                    self.check_and_solve_db_overflow()

            except KeyboardInterrupt:
                self.close_db_connection()
                self.dns_cache.dump()

            except IOError as e:
                if e.errno != errno.EINTR:
                    raise

    def handle_data(self, data):
        if data['event_type'] == 'dns' and data['dns']:
            return handle_dns(data, self.dns_cache)
        elif data['event_type'] == 'flow' and data['flow']:
            return handle_flow(data, self.traffic)
        elif data['event_type'] == 'tls' and data['tls']:
            return handle_tls(data, self.domain_replace, self.traffic)
        elif data['event_type'] == 'http' and data['http']:
            return handle_http(data, self.domain_replace, self.traffic)
        elif data['event_type'] == 'flow_start' and data['flow']:
            return handle_flow_start(data, self.allowed_interfaces, self.dns_cache, self.domain_replace, self.traffic)
        else:
            settings.logger.warning("Unknown event type.")

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
