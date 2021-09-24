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

## Schema

We should have schema in regard to normilize queries.

Query request schema:

```json
{
    "type": "object",
    "properties": {
        "hostname": {"type":"string"},
        "mac": {
            "type":"string",
            "pattern": "^(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$$"
        },
        "start": {"type": "string"},
        "end": {"type": "object"},
        "aggregate": {
            "type": "boolean",
            "enum": [true]
        }
    },
    "additionalProperties": false
}
```

For further details lookup the ``pakon-show`` command help. The __api__ implements pretty much same functionality.