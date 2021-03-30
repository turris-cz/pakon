# TODO: tests are not working, `app.session['logged']` not patched properly
import pytest


@pytest.mark.parametrize('query, cli_command', [
    ('', ['/usr/bin/pakon-show']),
    ('?number=15', ['/usr/bin/pakon-show', '-n', '15']),
    ('?page=1', ['/usr/bin/pakon-show', '-p', '1']),
    (
        '?number=16&page=2',
        ['/usr/bin/pakon-show', '-p', '2', '-n', '16']
    )
])
@pytest.mark.parametrize('logged_in', [True])
def test_correct_subprocess_called(
    client, fake_process, query, cli_command, logged_in
):
    """ Test if correct parameters are called with api call. """
    url_call = pytest.api_url + query
    res = client.get(url_call)
    assert res.data
    assert fake_process.calls[0] == cli_command


@pytest.mark.parametrize('query,logged_in', [({}, True)])
def test_parser_ignores_empty_lines(client, fake_process, query, logged_in):
    """ Test if cliParser class ignores empty values. """
    res = client.get(pytest.api_url)
    assert {} not in res.json


@pytest.mark.parametrize(
    'query, exp', [
        ('?number=10', 10),
        ('?page=2', 24),
        ('?page=2&number=5', 6)
    ]
)
def test_number_of_entries(client, fake_process, query, exp):
    """ exp: expected record return """
    url_call = pytest.api_url + query
    res = client.get(url_call)
    assert len(res.json) == exp
