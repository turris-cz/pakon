import pytest


@pytest.mark.parametrize('query', [{}])
def test_register_and_login(client, query, app):
    _sent = {"password": "secret"}
    res = client.post(pytest.pakon_url + 'register', json=_sent)
    assert res.json['success']
    res = client.post(pytest.pakon_url + 'login', json=_sent)
    assert res.json['success']
    assert client.session['logged']