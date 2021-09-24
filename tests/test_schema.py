import json
import pytest

def test_macaddr(client):
    res = client.post(pytest.api_url, json={"mac": "hh:bb:cc:xx:nn:zz"})
    assert "Failed validating" in res.json["error"]

def test_hostname(client):
    res = client.post(pytest.api_url, json={"hostname": 12456})
    assert "Failed validating" in res.json["error"]

def test_invalid_property(client):
    res = client.post(pytest.api_url, json={"foo": "bar"})
    assert "Additional properties are not allowed" in res.json["error"]

def test_invalid_date(client):
    res = client.post(pytest.api_url, json={"start": "1111-2021T11:11:11"})
    assert "Failed validating" in res.json["error"]