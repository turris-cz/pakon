from typing import List, Dict
from flask import request
import csv

from pakon_api.cli import COMMANDS

"""
Filters dictionary:
    'time': Amount in seconds of time the records are live.
    'count': count of entries that have to be fetched.
"""

csv.register_dialect('piper', delimiter='|', quoting=csv.QUOTE_NONE)


class utilParser:
    """ Utility more universal parser. """

    @staticmethod
    def _test_int(val):
        """ test if value is integer """
        try:
            return val
        except ValueError as e:
            # g.logger.error('Invalid number, %r' % e)
            pass

    @staticmethod
    def parse_query(args: List[str]):
        """ For each COMMAND item translate to argument and unwrap value. """
        return {
                trgt: utilParser._test_int(request.args.get(src))
                for (src, trgt) in COMMANDS.items()
                if args.get(src)
        }

    @staticmethod
    def unwrap_query(query: Dict[str, int]):
        """ Query data to command list. """
        res = []
        for key, value in query.items():
            res += [key]
            res += [value]
        return res


class cliParser:
    """ Dummy class to parse cli ontained data. """
    @staticmethod
    def _strip(data: List[str]) -> List[str]:
        """ Strip unnecessary spaces in captured output. """
        return [s.strip() for s in data]

    @staticmethod
    def _filter(data: Dict[str, str]) -> Dict[str, str]:
        """ Filter obtained data to only have appropriate content. """
        return {key: value for (key, value) in data.items() if key != '' and value != ''}  # noqa: E501

    @staticmethod
    def csv_to_json(input: str) -> List[Dict[str, str]]:
        data = []
        reader = csv.reader(input, dialect='piper')
        # get only header from top
        header = cliParser._strip(next(reader))
        for row in reader:
            data.append(cliParser._filter(dict(zip(header, cliParser._strip(row)))))  # noqa: E501
        # remove empty entries
        return [x for x in data if x]
