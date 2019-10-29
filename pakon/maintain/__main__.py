import argparse

from .archive import archive
from .backup import backup_sqlite
from .database import create_databases


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='action help', dest='action')
    subparsers.required = True

    subparsers.add_parser('create-databases', help='Create Pakon database from scratch')
    subparsers.add_parser('archive', help='Archive Pakon flows')
    subparsers.add_parser('backup', help='Backup Pakon flows')

    args = parser.parse_args()

    if args.action == 'create-databases':
        create_databases()
    elif args.action == 'archive':
        archive()
    elif args.action == 'backup':
        backup_sqlite()


if __name__ == '__main__':
    main()
