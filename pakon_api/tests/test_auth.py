import pytest
from flask import session


def test_register_and_login(client):
    _sent = {"password": "secret"}
    res = client.post(pytest.pakon_url + 'register', json=_sent)
    assert res.json['success']
    res = client.post(pytest.pakon_url + 'login', json=_sent)
    assert res.json['success']
    assert session['logged']


def test_already_registred(client, query):
    _sent = {"password": "secret"}
    res = client.post(pytest.pakon_url + 'register', json=_sent)
    assert res.json['success']
    _send_another = {"password": "another_password"}
    res = client.post(pytest.pakon_url + 'register', json=_send_another)
    assert res.json['error'] == 'admin already registered'


def test_logout(client, query):
    # TODO: make fixture user ``logged-in`` already
    _sent = {"password": "secret"}
    res = client.post(pytest.pakon_url + 'register', json=_sent)
    assert res.json['success']
    res = client.post(pytest.pakon_url + 'login', json=_sent)
    assert res.json['success']
    res = client.get(pytest.pakon_url + 'logout')
    assert session.get('logged', False) is False


@pytest.mark.parametrize('query', [('?number=10')])
def test_auth_fixture(client, query, auth, pakon_cli):
    assert session.get('logged', False) is False
    auth.login()
    assert session.get('logged', False) is True
    # TODO: res = client.get(pytest.api_url + query)
    auth.logout()
    assert session.get('logged', False) is False
