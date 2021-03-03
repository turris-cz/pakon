import pytest
from pakon_api.app import app


@pytest.fixture
def client(fake_process):
    with app.test_client() as client:
        fake_process.register_subprocess(
            ['/usr/bin/pakon-show', fake_process.any()]
        )
        yield client


@pytest.mark.parametrize('uri_call, cli_command', [
    ('/get/', ['/usr/bin/pakon-show']),
    ('/get/?time=254', ['/usr/bin/pakon-show', '-t', '254']),
    ('/get/?count=45', ['/usr/bin/pakon-show', '-c', '45']),
    (
        '/get/?time=254&count=45',
        ['/usr/bin/pakon-show', '-t', '254', '-c', '45']
    )
])
def test_correct_subprocess_called(
    client, fake_process, uri_call, cli_command
):
    res = client.get(uri_call)
    assert res.data
    assert fake_process.calls[0] == cli_command
