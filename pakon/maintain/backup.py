import logging
import os
import subprocess
import threading

logger = logging.getLogger(__name__)


def backup_sqlite():
    def backup_sqlite_thread():
        try:
            cmd = [
                "/usr/libexec/pakon-light/backup_sqlite.sh",
                "/var/lib/pakon.db",
                "/srv/pakon/pakon.db.xz",
            ]
            subprocess.call(cmd)
        except OSError as e:
            logger.warning("Failed to execute command: %r", e)

    os.makedirs("/srv/pakon", exist_ok=True)
    thread = threading.Thread(target=backup_sqlite_thread)
    thread.daemon = True
    thread.start()
