#!/usr/bin/env python3
import sys
import subprocess
import time
import datetime
import logging
from euci import EUci
from uci_tools import timestr_to_seconds
from db_handler import database, tables

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def squash(table, archive_table_name, rule):
    now = int(time.mktime(datetime.datetime.now().timetuple()))
    start = now - rule['up_to']
    for grouper in table.groupers(start):
        table.archive(grouper, start, rule)
    table.insert_to_archive(archive_table_name)
    table.delete_archived()

def load_archive_rules(src):
    lvl_rules = dict()
    i = 0
    while uci.get("{0}.@archive_rule[{1}].up_to".format(src, i)):
        level = uci.get("{0}.@archive_rule[{1}].level".format(src, i))
        up_to = uci.get_time("{0}.@archive_rule[{1}].up_to".format(src, i))
        window = uci.get_time("{0}.@archive_rule[{1}].window".format(src, i))
        size_threshold = int(uci.get("{0}.@archive_rule[{1}].size_threshold".format(src, i)) or 0)
        severity = uci.get("{0}.@archive_rule[{1}].severity".format(src, i)) or "*"
        category = uci.get("{0}.@archive_rule[{1}].category".format(src, i) or "")
        rule = {"up_to": up_to, "window": window, "size_threshold": size_threshold,
                "severity":severity, "category":category}
        if level not in lvl_rules:
            lvl_rules[level] = list()
            lvl_rules[level].append(rule)
        else:
            lvl_rules[level].append(rule)
        i = i + 1
    if not lvl_rules:
        lvl_rules.append({0:[{"up_to": 86400, "window": 60, "size_threshold": 4096 , "severity":"*", "category":"all"}]})
        logging.info("no rules in configuration - using default one")
    return lvl_rules


def main():
    with EUci() as uci:
        archive_path = uci.get(
            'pakon', 'archive', 'path',
            dtype=str,
            default='/srv/pakon/pakon-archive.db'
        )

        # maximum number of records in the live database - to prevent filling all available space
        # it's recommended not to touch this, unless you know really well what you're doing
        # filling up all available space may break your router
        hard_limit = uci.get(
            'pakon', 'archive', 'database_limit',
            dtype=int,
            default=10000000
        )
        flow_archive_keep = uci.get(
            "flow", "archive", "keep",
            dtype=str,
            default="4w"
        )
        alert_archive_keep = uci.get(
            "alert", "archive", "keep",
            dtype=str,
            default="4w"
        )

    _con = database.Database(archive_path)
    _con.attach_database("/var/lib/pakon.db", "live")
    _start = 3600*24 #move flows from live DB to archive after 24hours
    _now = int(time.mktime(datetime.datetime.now().timetuple()))
    # database connection, table name, details (dict(from:i, to:i+1)), list(grouperu)
    live_alert_table = tables.Alert(_con, logging, "live.alerts", {"from":None, "to":0})
    squash(live_alert_table, "alerts", {"up_to": _start, "window": 1, "size_threshold": 0, "severity":"*", "category":"all"})
    live_flow_table = tables.Flow(_con, logging, "live.traffic", {"from":None, "to":0})
    squash(live_flow_table, "traffic", {"up_to": _start, "window": 1, "size_threshold": 0, "severity":"*", "category":"all"})

    live_count = _con.select("select count(*) from live.traffic", None)[0][0]
    logging.info("{0} flows remaining in live database".format(live_count))

    # all changes in live database is done, backup it
    _con.dettach_database("live")
    subprocess.call(["/usr/libexec/pakon-light/backup_sqlite.sh", "/var/lib/pakon.db", "/srv/pakon/pakon.db.xz"])

    archive_count = _con.select("select count(*) from traffic", None)[0][0]
    rowids_to_del = None
    if archive_count > hard_limit:
        logging.warning('over {0} records in the archive database ({1}) -> deleting'.format(hard_limit, archive_count))
        rowids_to_del = _con.select("select rowid from traffic order by rowid desc limit -1 offset ?", (hard_limit, ))
    if rowids_to_del:
        _con.delete_in("traffic", "rowid", rowids_to_del)

    # UCI things
    alert_rules = load_archive_rules("alert")
    flow_rules = load_archive_rules("flow")
    #if the rules changed (there is detail level that can't be generated using current rules)
    #reset everything to detail level 0 -> perform the whole archivation again
    flow_lvl_highest = int(max(list(flow_rules.keys())))
    max_flow_level = int(_con.select("select max(details) from traffic", None)[0][0] or 0)
    if max_flow_level > flow_lvl_highest:
        logging.info("(flows):resetting all detail levels to 0")
        _con.update("update traffic set details = 0", None)

    alert_lvl_highest = int(max(list(flow_rules.keys())))
    max_alert_level = int(_con.select("select max(details) from alerts", None)[0][0] or 0)
    if max_alert_level > alert_lvl_highest:
        logging.info("(alerts):resetting all detail levels to 0")
        _con.update("update alerts set details = 0", None)

    for lvl, rules in flow_rules.items():
        for frule in rules:
            flow_table = tables.Flow(_con, logging, "traffic", {"from":int(lvl), "to":int(lvl)+1})
            squash(flow_table, "traffic", frule)
            f_count = _con.select("select count(*) from traffic where details = ?", (lvl, ))[0][0]
            logging.info("{0} flows remaining in archive on detail level {1}".format(f_count, lvl))

    for lvl, rules in alert_rules.items():
        for arule in rules:
            alert_table = tables.Alert(_con, logging, "alerts", {"from":int(lvl), "to":int(lvl)+1})
            squash(alert_table, "alerts", arule)
            a_count = _con.select("select count(*) from alerts where details = ?", (lvl, ))[0][0]
            logging.info("{0} alerts remaining in archive on detail level {1}".format(a_count, lvl))

    _con.update("delete from traffic where start < ?", (_now - timestr_to_seconds(flow_archive_keep), ))
    _con.update("delete from alerts where start < ?", (_now - timestr_to_seconds(alert_archive_keep), ))
    _con.close()


if __name__ == "__main__":
    main()
