import pytest


@pytest.mark.parametrize(
    "data,error_msg",
    [
        (
            {"mac": ["hh:bb:cc:xx:nn:zz"]},
            "'hh:bb:cc:xx:nn:zz' does not match",
        ),  # invalid mac
        ({"hostname": [12456]}, "12456 is not of type 'string'"),  # invalid hostname
        ({"foo": "bar"}, "Additional properties are not allowed"),  # invalid property
        (
            {"start": "1111-2021T11:11:11"},
            "1111-2021T11:11:11' does not match",
        ),  # invalid date
    ],
    indirect=False,
)
def test_wrong_data(client, data, error_msg):
    res = client.post(pytest.api_url, json=data)
    assert error_msg in res.json["error"]


def test_correct_filters(client):
    query = {
        "mac": ["11:22:33:44:55:66"],
        "hostname": ["google.com"],
        "start": "11-11-2011T11:11:11",
    }
    res = client.post(pytest.api_url, json=query)
    assert "error" not in res.json
