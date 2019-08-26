from .records import Record


class Table():
    """generic table
    """
    def __init__(self, database, logging, table, details):
        self.database = database
        self.table = table
        self.details = details
        self.to_del, self.to_ins = list(), list()
        self.logging = logging

    def groupers():
        pass

    def archive():
        pass

    def merge():
        pass

    def int_parse(self, *args):
        parsed = list()
        for arg in args:
            try:
                if arg:
                    parsed.append(int(arg))
                else:
                    parsed.append(0)
            except ValueError:
                raise Exception("valer")
            except TypeError:
                raise Exception("typer")
        return parsed

    def float_parse(self, *args):
        parsed = list()
        for arg in args:
            try:
                if arg:
                    parsed.append(float(arg))
                else:
                    parsed.append(0)
            except ValueError:
                raise Exception("valer")
            except TypeError:
                raise Exception("typer")
        return parsed

    def delete_archived(self):
        if not self.to_del:
            return
        del_dict = dict()
        for i, _del in enumerate(self.to_del):
            del_dict[str(i)] = _del
            # there is limit in sql bindings
            # so after 500 records it will
            # create another sql
            if i % 500 == 0:
                sql = "delete from {0} where rowid in ({1})".format(self.table, ", ".join(":{0}".format(d) for d in del_dict.keys()))
                self.database.update(sql, del_dict)
                del_dict = dict()
        if del_dict:
            sql = "delete from {0} where rowid in ({1})".format(self.table, ", ".join(":{0}".format(d) for d in del_dict))
            self.database.update(sql, del_dict)

    def insert_to_archive(self, archive_table):
        if not self.to_ins:
            return
        cols = list()
        placehold = list()
        vals = list()
        _val = dict()
        sample_rec = self.to_ins[0]
        for col, val in sample_rec.get_all().items():
            if col == "grouper":
                for column, value in val.items():
                    cols.append(column)
            else:
                cols.append(col)
        cols.append("details")
        for col in cols:
            placehold.append(":{0}".format(col))
        for ins in self.to_ins:
            for k, val in ins.get_all().items():
                if k == "grouper":
                    for column, value in val.items():
                        _val[column] = value
                else:
                    _val[k] = val
            _val['details'] = self.details['to']
            vals.append(_val)
            _val = dict()
        sql = "insert into {0} ({1}) values ({2})".format(archive_table,
                                                          ", ".join(str(col) for col in cols),
                                                          ", ".join(str(ph) for ph in placehold))
        self.database.execute_many(sql, vals)

class Flow(Table):
    """flows in traffic table"""
    def __init__(self, database, logging, table, details):
        Table.__init__(self, database, logging, table, details)

    def groupers(self, _start):
        """return unique indentifiers for flows to squash/group by them
        (src_mac, hostname)
        """
        to_ret = list()
        if self.details['from'] is not None:
            sql = str("select"
                      " distinct src_mac,"
                      " coalesce(app_hostname, dest_ip) as app_hostname"
                      " from {0}"
                      " where start < :start and details = :det")
        else:
            sql = str("select"
                      " distinct src_mac,"
                      " coalesce(app_hostname, dest_ip) as app_hostname"
                      " from {0}"
                      " where start < :start and flow_id is null")
        to_ret = self.database.select(sql.format(self.table), ({"start":_start,
                                                                "det":self.details['from']}))
        for i, ret in enumerate(to_ret):
            to_ret[i] = {"src_mac":ret['src_mac'], "app_hostname":ret['app_hostname']}
        return to_ret

    def archive(self, _grouper, _start, rule):
        results = list()
        if self.details['from'] is not None:
            results = self.database.select("select rowid,"
                                           " (start + duration) as end, *"
                                           " from traffic"
                                           " where src_mac = :mac"
                                           " and coalesce(app_hostname, dest_ip) = :host"
                                           " and start < :start"
                                           " order by dest_port, start",
                                           ({"mac":_grouper['src_mac'],
                                             "host":_grouper['app_hostname'],
                                             "start":_start}))
        else:
            results = self.database.select("select rowid,"
                                           " (start + duration) as end, *"
                                           " from live.traffic"
                                           " where src_mac = :mac"
                                           " and coalesce(app_hostname, dest_ip) = :host"
                                           " and start < :start and flow_id is null"
                                           " order by dest_port, start",
                                           ({"mac":_grouper['src_mac'],
                                             "host":_grouper['app_hostname'],
                                             "start":_start}))
        if not results:
            self.logging.warning("a rule ({0}) has no matches in database".format(rule))
            return
        prev_record = None
        for row in results:
            if row['rowid'] not in self.to_del:
                self.to_del.append(row['rowid'])
            start, end = self.float_parse(row['start'],
                                          row['end'])
            send, recv, window = self.int_parse(row['bytes_send'],
                                                row['bytes_received'],
                                                rule['window'])
            cur_record = Record(start, end, _grouper, row['src_ip'], row['src_port'], row['dest_ip']
                                , row['dest_port'], row['proto'], row['app_proto'], send, recv)
            if not prev_record:
                prev_record = cur_record
            elif prev_record.get('dest_port') == row['dest_port'] and prev_record.get('start') + prev_record.get('duration') + window > cur_record.get('start'):
                prev_record = self.merge(prev_record, cur_record)
            else:
                if prev_record.get('bytes_send') + prev_record.get('bytes_received') > rule['size_threshold']:
                    self.to_ins.append(prev_record)
                prev_record = cur_record
        self.to_ins.append(prev_record)

    def merge(self, prev, cur):
        """merge two records
        """
        if cur.get('start') + cur.get('duration') > prev.get('start') + prev.get('duration'):
            prev.dur_plus(cur.get('duration'))
        prev.set('bytes_send', (prev.get('bytes_send') + cur.get('bytes_send')))
        prev.set('bytes_received', (prev.get('bytes_received') + cur.get('bytes_received')))
        if prev.get('src_ip') != cur.get('src_ip'):
            prev.set('src_ip', '')
        if prev.get('dest_ip') != cur.get('dest_ip'):
            prev.set('dest_ip', '')
        if prev.get('app_proto') != cur.get('app_proto'):
            prev.set('app_proto', '')
        return prev


class Alert(Table):
    """alerts in alerts table
    """
    def __init__(self, database, logging, table, details):
        Table.__init__(self, database, logging, table, details)

    def groupers(self, _start):
        """return unique identifiers for alerts to squash/group by them
        (group id, signature id, rev, signature, category, severity)
        """
        to_ret = list()
        if self.details['from'] is not None:
            sql = str("select distinct gid,"
                      " sid, rev, signature, category, severity"
                      " from {0} where start < :start"
                      " and details = :det")
        else:
            sql = str("select distinct gid,"
                      " sid, rev, signature, category, severity"
                      " from {0} where start < :start")
        to_ret = self.database.select(sql.format(self.table), ({"start":_start,
                                                                "det":self.details['from']}))
        for i, ret in enumerate(to_ret):
            to_ret[i] = {"gid":ret['gid'], "sid":ret['sid'], "rev":ret['rev'],
                         "signature":ret['signature'], "category":ret['category'],
                         "severity":ret['severity']}
        return to_ret

    def archive(self, _grouper, _start, rule):
        results = list()
        data_bind = {
            "sid":_grouper['sid'],
            "sig":_grouper['signature'],
            "sev":None,
            "cat":None,
            "det":self.details['from'],
            "start":_start
        }
        if self.details['from'] is not None:
            sql = str("select rowid, * from {0}"#alerts
                      " where sid = :sid and signature = :sig"
                      "  {1} {2}"
                      " and details = :det and start < :start order by dest_port, start")
        else:
            sql = str("select rowid, * from {0}"#live.alerts
                      " where sid = :sid and signature = :sig"
                      " {1} {2}"
                      " and start < :start order by dest_port, start")
        sql, data_bind = self.sev_cat_handle(rule['severity'], rule['category'], sql, data_bind)
        results = self.database.select(sql.format(self.table), (data_bind))
        if not results:
            self.logging.warning("a rule ({0}) has no matches in database".format(rule))
            return
        prev_record = None
        for row in results:
            row = dict(row)
            if row['rowid'] not in self.to_del:
                self.to_del.append(row['rowid'])
            if "duration" not in row.keys():
                row['duration'] = 0
            start = self.float_parse(row['start'])[0]
            send, recv = self.int_parse(row['bytes_send'], row['bytes_received'])
            window, duration = self.int_parse(rule['window'], row['duration'])
            end = start + duration
            cur_record = Record(start, end, _grouper, row['src_ip'],
                                row['src_port'], row['dest_ip'], row['dest_port'],
                                row['proto'], row['app_proto'], send, recv)
            if not prev_record:
                prev_record = cur_record
            elif prev_record.get('dest_port') == row['dest_port'] and prev_record.get('start') <= cur_record.get('start') and prev_record.get('start') + window >= cur_record.get('start'):
                prev_record = self.merge(prev_record, cur_record)
            else:
                if int(prev_record.get('bytes_send')) + int(prev_record.get('bytes_received')) > rule['size_threshold']:
                    self.to_ins.append(prev_record)
                prev_record = cur_record
        self.to_ins.append(prev_record)

    def merge(self, prev, cur):
        """merge two records
        """
        if cur.get('start') > prev.get('start'):
            prev.dur_plus(int(cur.get('start')) - int(prev.get('start')))
        prev.set('bytes_send', (prev.get('bytes_send') + cur.get('bytes_send')))
        prev.set('bytes_received', (prev.get('bytes_received') + cur.get('bytes_received')))
        if prev.get('src_ip') != cur.get('src_ip'):
            prev.set('src_ip', '')
        if prev.get('dest_ip') != cur.get('dest_ip'):
            prev.set('dest_ip', '')
        if prev.get('app_proto') != cur.get('app_proto'):
            prev.set('app_proto', '')
        return prev

    def sev_cat_handle(self, severity, category, sql, data_bind):
        """handle severity and category inputs and insert them into sql
        """
        if "*" in severity:
            # empty where statement
            sev = ""
        elif "," in severity:
            severities = severity.split(',')
            _in = ", ".join(":{0}".format(s) for s in severities)
            sev = " and severity in ({0})".format(_in)
            for bind_s in severities:
                if bind_s.isdigit():
                    data_bind[bind_s] = bind_s
                else:
                    raise TypeError("severity - unparsable value ({0})".format(severity))
        elif "<" in severity:
            sev = " and severity < :sev"
            data_bind['sev'] = int(severity.split('<')[1].strip())
        elif ">" in severity:
            sev = " and severity > :sev"
            data_bind['sev'] = int(severity.split('>')[1].strip())
        else:
            if severity.isdigit():
                sev = " and severity = :sev"
                data_bind['sev'] = int(severity)
            else:
                raise TypeError("severity - unparsable value ({0})".format(severity))
        if "all" in category:
            # empty where statement
            cat = ""
        elif "," in category:
            categories = category.split(',')
            _in = ", ".join(":{0}".format(c) for c in categories)
            cat = " and category in ({0})".format(_in)
            for bind_c in categories:
                data_bind[bind_c] = bind_c
        else:
            cat = " and category = :cat"
            data_bind['cat'] = category
        sql = sql.format(self.table, sev, cat)
        return (sql, data_bind)
