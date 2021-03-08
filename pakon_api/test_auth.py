import pytest


@pytest.mark.parametrize('query', [{}])
def test_register_password(client, query, app):
    _sent = {"password": "secret"}
    res = client.post(pytest.pakon_url + 'register', json=_sent)
    assert res.json != _sent
    assert False