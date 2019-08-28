#!/usr/bin/env python3
import sys
import subprocess
import time
import datetime
import logging
from db_handler import database, tables

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

#TODO: replace with uci bindings - once available
def uci_get(opt):
    delimiter = '__uci__delimiter__'
    chld = subprocess.Popen(['/sbin/uci', '-d', delimiter, '-q', 'get', opt],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, _ = chld.communicate()
    out = out.strip().decode('ascii', 'ignore')
    if out.find(delimiter) != -1:
       return out.split(delimiter)
    return out

def uci_get_time(opt, default=None):
    ret = 0
    text = uci_get(opt)
    if not text:
        text = default
    if text[-1:].upper() == 'M':
        ret = int(text[:-1]) * 60
    elif text[-1:].upper() == 'H':
        ret = int(text[:-1]) * 3600
    elif text[-1:].upper() == 'D':
        ret = int(text[:-1]) * 24 * 3600
    elif text[-1:].upper() == 'W':
        ret = int(text[:-1]) * 7 * 24 * 3600
    else:
        ret = int(text)
    return ret

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
    while uci_get("{0}.@archive_rule[{1}].up_to".format(src, i)):
        level = uci_get("{0}.@archive_rule[{1}].level".format(src, i))
        up_to = uci_get_time("{0}.@archive_rule[{1}].up_to".format(src, i))
        window = uci_get_time("{0}.@archive_rule[{1}].window".format(src, i))
        size_threshold = int(uci_get("{0}.@archive_rule[{1}].size_threshold".format(src, i)) or 0)
        severity = uci_get("{0}.@archive_rule[{1}].severity".format(src, i)) or "*"
        category = uci_get("{0}.@archive_rule[{1}].category".format(src, i) or "")
        rule = {"up_to": up_to, "window": window, "size_threshold": size_threshold,
                "severity":severity, "category":category}
        if level not in lvl_rules:
            lvl_rules[level] = list()
            lvl_rules[level].append(rule)
        else:
            lvl_rules[level].append(rule)
        i = i + 1
    if lvl_rules:
        for rules in lvl_rules.values():
            rules = sorted(rules, key=lambda r: r['up_to'])
    else:
        lvl_rules.append({0:[{"up_to": 86400, "window": 60, "size_threshold": 4096 , "severity":"*", "category":"all"}]})
        logging.info("no rules in configuration - using default {0}".format(str(rules[0])))
    return lvl_rules


def main():
    archive_path = uci_get('pakon.archive.path') or '/srv/pakon/pakon-archive.db'
    _con = database.Database(archive_path)
    _con.attach_database("/var/lib/pakon.db", "live")
    _start = 0#test reason - 3600*24 #move flows from live DB to archive after 24hours
    _now = int(time.mktime(datetime.datetime.now().timetuple()))
    # database connection, table name, details (dict(from:i, to:i+1)), list(grouperu)
    live_alert_table = tables.Alert(_con, logging, "live.alerts", {"from":None, "to":0})
    squash(live_alert_table, "alerts", {"up_to": _start, "window": 1, "size_threshold": 0, "severity":"*", "category":"all"})
    live_flow_table = tables.Flow(_con, logging, "live.traffic", {"from":None, "to":0})
    squash(live_flow_table, "traffic", {"up_to": _start, "window": 1, "size_threshold": 0, "severity":"*", "category":"all"})

    # maximum number of records in the live database - to prevent filling all available space
    # it's recommended not to touch this, unless you know really well what you're doing
    # filling up all available space may break your router
    hard_limit = int(uci_get('pakon.archive.database_limit') or 10000000)
    live_count = _con.select("select count(*) from live.traffic", None)[0][0]
    logging.info("{0} flows remaining in live database".format(live_count))

    # all changes in live database is done, backup it
    _con.dettach_database("live")
    subprocess.call(["/usr/libexec/bckp_pakon/backup_sqlite.sh", "/var/lib/pakon.db", "/srv/pakon/pakon.db.xz"])

    archive_count = _con.select("select count(*) from traffic", None)[0][0]
    rowids_to_del = None
    # TODO rewrite old method sel_sing_table to newer one (select)
    if archive_count > hard_limit:
        logging.warning('over {0} records in the archive database ({1}) -> deleting'.format(hard_limit, archive_count))
        rowids_to_del = _con.select_single_table("traffic", "rowid", orderby="rowid desc limit -1 offset {0}".format(hard_limit))
    if rowids_to_del:
        _con.delete_in("traffic", "rowid", rowids_to_del)

    # UCI things
    alert_rules = load_archive_rules("alert")
    flow_rules = load_archive_rules("flow")
    #if the rules changed (there is detail level that can't be generated using current rules)
    #reset everything to detail level 0 -> perform the whole archivation again
    max_flow_level = _con.select("select max(details) from traffic", None)[0][0] or 0
    if max_flow_level > len(flow_rules):
        logging.info("(flows):resetting all detail levels to 0")
        _con.update("update traffic set details = 0", None)
    max_alert_level = _con.select("select max(details) from alerts", None)[0][0] or 0
    if max_alert_level > len(alert_rules):
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

    _con.update("delete from traffic where start < ?", (_now - uci_get_time("flow.archive.keep", "4w"), ))
    _con.update("delete from alerts where start < ?", (_now - uci_get_time("alert.archive.keep", "4w"), ))
    _con.close()
if __name__ == "__main__":
    main()
