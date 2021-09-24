# Pakon API

Project to wrap Pakon-CLI output to JSON response and provide it as HTTP service for (prefarably) React web UI.

This branch of Pakon-light is pure flask app. Considering to use application spawner.

## Development

You are able to run code on router to play with the code. Just make sure you have pakon installed.

note: better run code in somekind of virtual environment

Run as a simple flask application. For development install:

    pip install flask

Set ``FLASK_APP`` env-var than run:

    export FLASK_APP=pakon-api
    flask run

In case you need to expose further than `localhost` set address

    flask run --host 0.0.0.0

## Schema

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