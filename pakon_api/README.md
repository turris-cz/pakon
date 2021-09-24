# Pakon API

This project only covers the layer that serves as bridge between frontend and ``pakon`` package. Queries are pretty much untouched (except for ``time`` which requires special handling.)

Implemented as bare flask application.

## Development

Do not need to install locally or do some preparations. 
Copy to router (``/tmp``, whatever), make sure you have ``pip3`` installed

    /tmp# opkg install python3-pip
    /tmp# cd pakon-api
    /tmp/pakon-api# pip install -e .

Set ``FLASK_APP`` env-var than run.

    export FLASK_APP=pakon-api
    flask run --host 0.0.0.0

In case you need to expose service further than `localhost` (on router) set ``--host`` to ``0.0.0.0``

You may override default port, you don't have to neccesarilly.

### Example query

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
