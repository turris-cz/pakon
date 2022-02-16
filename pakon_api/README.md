# Pakon API

This project only covers the layer that serves as the bridge between the frontend and ``pakon`` package. Queries are pretty much untouched (except for ``time``, which requires special handling.)

It is implemented as bare flask application.

## Development

| :exclamation: These upcoming steps need to be executed on the router.  |
|-----------------------------------------|

| :zap:        Do not install it locally on your computer or even do some preparations.  |
|-----------------------------------------|

1. Download this project

This could be done in multiple ways. 

For example, you can download this repository using buttons provided by UI (GitLab/GitHub) and then move it by SCP using third-party software like FileZilla, WinSCP, etc. to folder /tmp on the router.

The better way to connect to your router is to use the SSH protocol. On any GNU/Linux distributions, you need to open the terminal and proceed with the following commands:

```
ssh root@ipaddress
opkg update
opkg install git-http
cd /tmp
git clone address-of-this-repository
```

By running the last command, it will download not only files responding to fetch and pull files, but this package also depends on the git package to be able to clone it. 

Usually, it is better to store things in ``/tmp`` (which is in RAM) to avoid unnecessary writes to the internal storage.

Once you manage to be in the folder ``/tmp``, you can clone this repository.

2. Install pip

We need to install this package locally by using pip. This can be done as previously mentioned by ``opkg`` the package manager on OpenWrt.

```
opkg install python3-pip
```

3. Install this project

We need to enter the project folder by using Linux command ``cd``. After that, we can use pip to install it.

```
cd pakon
pip install -e .
```

4. Export variables to the terminal

Set ``FLASK_APP`` by using following command:

```
export FLASK_APP=pakon_api
```

5. Start flask
```
flask run --host 0.0.0.0
```
 
In case you need to expose service further than `localhost` (on router) set ``--host`` to ``0.0.0.0``

You may override the default port. You don't have to necessarily.

## Verify that it works

Postman TO-DO

### Send query

Example query:

post below json to serving host

```json
{
    "mac":["c7:18:ba:b8:14:7d"],
    "start":"25-09-2021T11:30:00",
    "end":"26-09-2021T11:11:11"
}
```

## Query schema

We should have schema in regard to normilize queries.
Query request schema:

```json
{
    "definitions": {
        "time": {
            "type": "string",
            "pattern": "^(?:[0-9]{2}-){2}[0-9]{4}(?:T(?:[0-9]{2}:){2}[0-9]{2})?$"
        }
    },
    "type": "object",
    "properties": {
        "hostname": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": "^[a-z.-]+$"
            }
        },
        "mac": {
            "type": "array",
            "items": {
                "type":"string",
                "pattern": "^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$$"
            }
        },
        "start": {"$ref": "#/definitions/time"},
        "end": {"$ref": "#/definitions/time"},
        "aggregate": {
            "type": "boolean",
            "enum": [true]
        }
    },
    "additionalProperties": false
}
```

For further details lookup the ``pakon-show`` command help. The __api__ implements pretty much same functionality.

## Response schema

Response from backend is list of table rows. The columns are following:

- datetime 
- dur (duration in seconds)
- src MAC (source MAC)
- hostname (ip as fallback)
- dst port
- proto (protocol)
- sent (in KiB)
- recvd (received in KiB)
