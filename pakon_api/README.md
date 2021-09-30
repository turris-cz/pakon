# Pakon API

Project to provide pakon collected data to frontend.

This branch is pure flask app. Consider usíng application spawner.

## Development

Run as a simple flask application. For development install:

    pip install flask

Set ``FLASK_APP`` env-var than run:

    export FLASK_APP=pakon-api
    flask run

In case you need to expose further than `localhost` (on router) set address

    flask run --host 0.0.0.0

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

For further details lookup the ``pakon-show`` command help. The __api__ implements pretty much same functionality.