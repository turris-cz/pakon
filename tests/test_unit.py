import pytest

from pakon_api.utils import json_query


def test_long_time():
    query = {"start": "11-11-2011T11:11:11"}
    result = """{"start": 1321006271}\n"""
    res = json_query(query)
    assert res.decode() == result


def test_short_time():
    query = {"end": "11-11-2011"}
    result = """{"end": 1320966000}\n"""
    res = json_query(query)
    assert res.decode() == result
