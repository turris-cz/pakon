from pakon_api.utils import cliParser, utilParser
from pakon_api.cli import run_show


def fetch_data(_filters):
    data = run_show(utilParser.unwrap_query(_filters))
    return cliParser.csv_to_json(data)


def process_query(args):
    return utilParser.parse_query(args)
