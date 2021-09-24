# Pakon
## Introduction
Pakon is a system for monitoring network traffic. It basically collects and stores network flows, but enriched with app-level hostname ("user-treated hostname"). It consists of several componenents and pieces of software. 

The next part aims to give an high-level overview of components. In the following parts, the databases are explained and then the datails of inividual components are described.

## Overview of architecture

At first, data about network traffic has to be captured. We use **Suricata** for that. Suricata is able to provide information about network flows, as well as some aditional information from deep-packet inspection (HTTP and TLS headers, DNS queries and responses). But that pieces of information are not correlated - e.g. we get information about DNS query&response and then about network flow (destined for the IP got from the DNS query). We want to show that the IP is actually the hostname got earlier from the DNS query. This feature is not provided by suricata, so we use another piece of software for that. Data provided by suricata are in JSON-format, much better then raw (pcap?) data, but they still need some processing.

Data from Suricata are sent to unix-socket (datagram) and they are received and processed by **pakon-monitor**. Pakon-monitor stores network flows in sqlite database (referred to as *live* database, see below). It uses additional information from suricata to enrich the flows (specifically, it tries to assign hostname - from DNS information, HTTP&TLS headers and so on). After being processed by pakon-monitor, data are safely and happily stored in a database. But the problem is that the database may grow very fast into a big size. That's where the aggregation comes into play.

We need to squeeze the data to be able to store them for a longer time. That's the task of **pakon-archive** script. That script takes data from *live* database and moves them to *archive* database. Only moving of course won't reduce the size. We observed, that typically there is many simultaneous connections to one host. The archivation exploits that. Simultanous connections to one host (from the same source and on the same port) are squeezed into just one connection - where the data transfered is the sum of data transferred in individual connections and the duration is from the start of the earliest connection till the end of the last (simultaneous) connection. In other words, archivation basically solves *Overlapping intervals* problem - with respect to source (src_mac), destination and destination ports.

As described earlier, the data are stored in a pretty standard sqlite database, so it would be possible to show the data straight from that database. But we actually have two sqlite databases. To hide the complexity of that, we also have one daemon **pakon-handler** to query data from the database. It has its own unix-domain socket, where it accepts queries and responds to them with data. The queries can be also used to filter the data - filering by time, source or destination.

## Details

### Used databases

As mentioned earlier, there are two sqlite databases used.

One is called **live** database. That's the one where the data are stored immediately upon capturing, without much processing or archivation. Many INSERTs (new flows) and UPDATEs (new information about flow) is expected. Thus, the database is changing very often and we can't do many writes to flash memory. Because of that, this database lives in tmpfs (`/var/lib/pakon.db`) and it's backed up periodically (now every 8 hours, by cron) to permanent storage (`/srv/pakon/pakon.db.xz`). When *pakon-monitor* service starts, it extracts database from `/srv/pakon/pakon.db.xz` to `/var/lib/pakon.db`. When it stops (e.g. before reboot), it backups `/var/lib/pakon.db` to `/srv/pakon/pakon.db.xz`. 

The second one is called **archive** database. It's stored in permanent storage (`/srv/pakon/pakon-archive.db`) and it's expected it will be written rarely, only when archivation runs (once daily now). Data in this database are aggregated, simultaneous connections are squeezed into one.


### Software components in higher detail

#### Suricata

We use standard Suricata with a few minor patches. The most important one for *pakon-monitor* is patch that adds flow_start event. Normally, suricata just outputs information about flow when it ends - but this can take quite a long time, we want to know as soon as possible - to store also the details (app_hostname) as soon as possible. There are also patches for logging MAC addresses and including a directory into a config file - which is handy for our way of packaging.


#### Pakon-monitor

Pakon-monitor collects all event from suricata. It maintains a small cache of last-seen DNS responses. When it sees a new flow, it look for the destination IP in the DNS cache and tries to find the hostname. If that succeds, it also stores that name as the app_hostname. The database is backed up/restored when the service stops/starts.

Even if the name is not found in the DNS cache, it may be later filled in from deep-packet inspection done by suricata - e.g. from TLS SNI.

Only the traffic originating from allowed interfaces (LAN by default - `br-lan`) is stored. This is because the MAC adress is the primary identifier of the source. MAC adresses on WAN are probably not very useful.

Apart from the main purpose of storing all data from suricata into the sqlite database, *pakon-monitor* also does several other things:
 - **replacing hostnames** - e.g. `*fbcdn.net` is replaced by `facebook.com`. We feel this is more what the user expects and it also promotes the effects of aggregation. The lists are provided by *pakon-lists* package.
 - **notifications about new devices (unknown MAC addresses)** - when `pakon.monitor.notify_new_devices` is set
 - **keeping the *live* database in sane size limits** - when the database exceeds hard limit (3M records by default), the oldest records are deleted. This is to prevent filling up the whole tmpfs.
 
#### Pakon-archive

Pakon-archive moves the data from *live* database to *archive* database. It also aggregates them to allow storing them for a longer time. Several aggregation levels exists.

The basic idea of aggregation is squeezing simultaneous connections into one. For example, if we have two flows to `example.com`:
 1. starting at time 1, ending at time 5 and transfering 1MB/1MB and 
 2. starting at time 4, ending at time 15 and transfering 2MB/2MB

the resulting flow after aggregation would be one flow starting at time 1, ending at time 15 and transfering 3MB/3MB.

The higher aggregation level (typically applied after a longer time) allows to squeeze connections that are not simultaneous, but just *close enough*. It's defined by time window. For example, when the time window is 300 (seconds) and we have two flows to `example.com`:
 1. starting at time 1, ending at time 10 and transfering 100MB/100MB and 
 2. starting at time 311, ending at time 600 and transfering 200MB/200MB

they will be merged together as well, resulting in one flow starting at time 1, ending at time 600 and transfering 300MB/300MB.

Thanks to that principle, all flows in *archive* database are non-overlapping - i.e. at any moment, there is at most one flow from a specific source to a specific destination (and destination port). It's useful for displaying data - as we will see in the next part.

**A note about app_hostname** - instead of just using `app_hostname` collumn, we use `COALESCE(app_hostname,dest_ip)` - hostname or dest_ip (if hostname is not known). This applies for pakon-handler as well.

Some higher aggregation levels also have size_threshold defined, this is to delete very small flows. This is particularly useful with P2P traffic - we observed these services often creates connection and transfer no data in the end.

Finally, pakon-archive deletes data older than `pakon.archive.keep`.

#### Pakon-handler

Pakon-handler gets the data from both *live* and *archive* database and serves them to frontend (web-ui or pakon-show). To reduce the amount of data we serve the user, we want to merge simultaneous connections (the same thing we do in archivation). This property is fullfilled for data from *archive* database, but not for data from *live* database. So pakon-handler basically performs aggregation of data from *live* database first (in memory, without modifying the database).

Pakon-handler has two modes: timeline and aggregated data. The first (timeline) preserves start time of connections, so you get a list of network flows ordered by time. A single destination may appear many times. In aggregated mode, a single destination appears at most once (for each src_mac). Note that the agregation described in the previous paragraph happens always, regardless of whether the aggregated mode is requested - that is to squeeze simulataneous connection, aggregated mode in the query has a different meaning.

Pakon-handler also doesn't show all the records by default. We observed that many connections are to ad-servers, tracking and so on, which is probably not useful for most of the users. So pakon-handler by default hides domains specified in domains_ignore in *pakon-lists* package. This behavior can be turned off by passing `filter: false` parameter in the query.
# pakon-api

simple pakon api
