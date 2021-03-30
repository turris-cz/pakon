import os
import pytest
from pakon_api.pakon_api import create_app
import tempfile


def pytest_configure():
    pytest.api_url = '/pakon/api/get/'
    pytest.pakon_url = '/pakon/'


def _split_query(query):
    """ Helper function to simulate query. """
    queries = query.strip("?").split("&")
    _filters = {}
    for query in queries:
        key, value = query.split("=")
        _filters.update({key: int(value)})
    return _filters


def _load_command_result(query):
    """ Helper function to simulate `pakon-show` parameters. """
    data = []
    with open('pakon_api/tests/test_files/pakon-show') as f:
        data = f.read().split('\n')
    if not query:
        return data
    fltr = _split_query(query)
    if 'page' in fltr:
        split = len(data)//2
        data = (data[:split], data[split:])[fltr['page']-1]
    if 'number' in fltr:
        data = data[:fltr["number"]+2]
    return data


@pytest.fixture(scope='function')
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path})
    with app.app_context():
        yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(params="query")
def query(request):
    # TODO: make empty query default
    # see parametrize decorator of func `test_parser_ignores_empty_lines()`
    # there is redundant empty query dict
    if type(request.param) is not dict:
        return None
    return _split_query(request.param)


@pytest.fixture(scope='function')
def client(app):
    """ Fixture to wrap flask client. Provides test function access to api and
wraps client in correct app_context. """
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def pakon_cli(fake_process, query):
    """ Fake process. """
    fake_process.register_subprocess(
        ['/usr/bin/pakon-show', fake_process.any()],
        stdout=_load_command_result(query)
    )
    yield fake_process


class AuthActions:
    """ Authorization actions helper class. """
    def __init__(self, client):
        self._client = client

    def login(self):
        _sent = {"password": "secureandsecret"}
        self._client.post(pytest.pakon_url + 'register', json=_sent)
        return self._client.post(pytest.pakon_url + 'login', json=_sent)

    def logout(self):
        return self._client.get(pytest.pakon_url + 'logout')


@pytest.fixture()
def auth(client):
    """ Authorization fixture. """
    return AuthActions(client)
