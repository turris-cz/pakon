import pytest
from flask import session


@pytest.mark.parametrize('query', [{}])
def test_register_and_login(client):
    _sent = {"password": "secret"}
    res = client.post(pytest.pakon_url + 'register', json=_sent)
    assert res.json['success']
    res = client.post(pytest.pakon_url + 'login', json=_sent)
    assert res.json['success']
    assert session['logged']


@pytest.mark.parametrize('query', [{}])
def test_already_registred(client, query):
    _sent = {"password": "secret"}
    res = client.post(pytest.pakon_url + 'register', json=_sent)
    assert res.json['success']
    _send_another = {"password": "another_password"}
    res = client.post(pytest.pakon_url + 'register', json=_send_another)
    assert res.json['error'] == 'admin already registered'


@pytest.mark.parametrize('query', [{}])
def test_logout(client, query):
    # TODO: make fixture user ``logged-in`` already
    _sent = {"password": "secret"}
    res = client.post(pytest.pakon_url + 'register', json=_sent)
    assert res.json['success']
    res = client.post(pytest.pakon_url + 'login', json=_sent)
    assert res.json['success']
    res = client.get(pytest.pakon_url + 'logout')
    assert session['logged'] is False
