import pytest

# TODO: test queries?


def test_basic(mock_socket, client):
    res = client.post(pytest.api_url, json={})
    assert res
