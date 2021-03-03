from pakon_api.utils import cliParser, utilParser
from pakon_api._cli import _run_show


def fetch_data(filter):
    return cliParser.csv_to_json(_run_show(filter))


def process_query(args):
    return utilParser.parse_query(args)
