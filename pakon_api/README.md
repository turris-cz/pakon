# Pakon API

This project only covers the layer that serves as the bridge between the frontend and ``pakon`` package. Queries are pretty much untouched.

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

## Send query

send ``POST`` request onto

```
http://<router-ip>/pakon/api/query
```

Having ``BODY`` of the request as json defined by query schema defined in [pakon_query.json](schema/pakon_query.json)

Example query:

```json
{
    "mac":["c7:18:ba:b8:14:7d"],
    "start": 1651730157,
    "end": 1651732243
}
```

### Query paramters

| parameter  | data type      | description                                      |
|------------|----------------|--------------------------------------------------|
| hostname   | str[]          | list of remote hostnames accessed by local user  |
| mac        | str[], mac     | list of mac addresses you need to inspect        |
| start, end | int, timestamp | parameters to filter on given time span          |
| aggregate  | boolean        | True to aggregate with historical data           |


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
