class Record():
    """generic object in database
    """
    def __init__(self, start, end, grouper, src_ip, src_port, dest_ip, dest_port, proto, app_proto, bytes_send, bytes_recv):
        if end == 0:
            duration = end
        else:
            duration = int(end)-int(start)
        self.rec = {
            "start":start,
            "duration":duration,
            "grouper":grouper,
            "src_ip":src_ip,
            "src_port":src_port,
            "dest_ip":dest_ip,
            "dest_port":dest_port,
            "proto":proto,
            "app_proto":app_proto,
            "bytes_send":bytes_send,
            "bytes_received":bytes_recv
        }

    def get_all(self):
        return self.rec

    def get(self, item):
        return self.rec[item]

    def set(self, item, value):
        self.rec[item] = value

    def dur_plus(self, dur):
        self.rec['duration'] += dur
