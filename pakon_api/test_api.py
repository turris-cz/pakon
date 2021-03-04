import pytest
from pakon_api.app import app

_URL = ('/pakon/api/get/')


def _load_command_result():
    with open('pakon_api/test_files/pakon-show') as f:
        return f.read().split('\n')


@pytest.fixture
def client(fake_process):
    with app.test_client() as client:
        with app.app_context():
            fake_process.register_subprocess(
                ['/usr/bin/pakon-show', fake_process.any()],
                stdout=_load_command_result()
            )
            yield client


@pytest.mark.parametrize('query, cli_command', [
    ('', ['/usr/bin/pakon-show']),
    ('?time=254', ['/usr/bin/pakon-show', '-t', '254']),
    ('?count=45', ['/usr/bin/pakon-show', '-c', '45']),
    (
        '?time=254&count=45',
        ['/usr/bin/pakon-show', '-t', '254', '-c', '45']
    )
])
def test_correct_subprocess_called(
    client, fake_process, query, cli_command
):
    url_call = _URL + query
    res = client.get(url_call)
    assert res.data
    assert fake_process.calls[0] == cli_command


def test_parser_ignores_empty_lines(client, fake_process):
    res = client.get(_URL)
    assert {} not in res.json
