# TODO: tests are not working, `app.session['logged']` not patched properly
import pytest


# @pytest.fixture
# def login(client):
#     _sent = {"password": "secureandsecret"}
#     client.post(pytest.pakon_url + 'register', json=_sent)
#     client.post(pytest.pakon_url + 'login', json=_sent)
#     yield
#     client.post(pytest.pakon_url + 'logout')


# @pytest.mark.parametrize('query, cli_command', [
#     ('', ['/usr/bin/pakon-show']),
#     ('?number=15', ['/usr/bin/pakon-show', '-n', '15']),
#     ('?page=1', ['/usr/bin/pakon-show', '-p', '1']),
#     (
#         '?number=16&page=2',
#         ['/usr/bin/pakon-show', '-p', '2', '-n', '16']
#     )
# ])
# def test_correct_subprocess_called(
#     client, pakon_cli, query, cli_command, # login / auth
# ):
#     """ Test if correct parameters are called with api call. """
#     # auth.login()
#     url_call = pytest.api_url + query
#     res = client.get(url_call)
#     assert res.data
#     assert pakon_cli.calls[0] == cli_command


# @pytest.mark.parametrize('query', [{}])
# def test_parser_ignores_empty_lines(client, pakon_cli, query):
#     """ Test if cliParser class ignores empty values. """
#     res = client.get(pytest.api_url)
#     assert {} not in res.json


# @pytest.mark.parametrize(
#     'query, exp', [
#         ('?number=10', 10),
#         ('?page=2', 24),
#         ('?page=2&number=5', 6)
#     ]
# )
# def test_number_of_entries(client, pakon_cli, query, exp):
#     """ exp: expected record return """
#     url_call = pytest.api_url + query
#     res = client.get(url_call)
#     assert len(res.json) == exp
