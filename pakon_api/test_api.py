import pytest
from pakon_api.app import app


_URL = '/pakon/api/get/'


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
    with open('pakon_api/test_files/pakon-show') as f:
        data = f.read().split('\n')
    if not query:
        return data
    fltr = _split_query(query)
    if 'number' in fltr:
        retval = data[:fltr["number"]+1]
        return retval
    if 'page in fltr':
        split = len(data)//2
        return(data[:split], data[split:])[fltr['page']-1]


@pytest.fixture
def query(request):
    yield _split_query(request.param)


@pytest.fixture
def client(fake_process, query):
    """ Fixture to wrap flask client. Provides test function access to api and
wraps client in correct app_context. """
    with app.test_client() as client:
        with app.app_context():
            fake_process.register_subprocess(
                ['/usr/bin/pakon-show', fake_process.any()],
                stdout=_load_command_result(query)
            )
            yield client


@pytest.mark.parametrize('query, cli_command', [
    ('', ['/usr/bin/pakon-show']),
    ('?number=15', ['/usr/bin/pakon-show', '-n', '15']),
    ('?page=1', ['/usr/bin/pakon-show', '-p', '1']),
    (
        '?number=16&page=2',
        ['/usr/bin/pakon-show', '-p', '2', '-n', '16']
    )
])
def test_correct_subprocess_called(
    client, fake_process, query, cli_command
):
    """ Test if correct parameters are called with api call. """
    url_call = _URL + query
    res = client.get(url_call)
    assert res.data
    assert fake_process.calls[0] == cli_command


def test_parser_ignores_empty_lines(client, fake_process):
    """ Test if cliParser class ignores empty values. """
    res = client.get(_URL)
    assert {} not in res.json


@pytest.mark.parametrize(
    'query, exp', [
        ('?number=10', 10),
        ('?page=2', 16)
    ]
)
def test_number_of_entries(client, fake_process, query, exp):
    """ exp: expected result count """
    url_call = _URL + query
    res = client.get(url_call)
    assert len(res.json) == exp
