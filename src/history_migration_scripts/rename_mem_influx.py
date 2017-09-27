from itertools import imap
from pprint import pprint

from influxdb import InfluxDBClient


def delete_kb():
    client = InfluxDBClient("vm166.jinr.ru", database="icinga2")
    client.query("DROP SERIES FROM check_openvz_vm_perf WHERE metric =~ /mem_kb_.*/")
    print 'done'

def main():
    client = InfluxDBClient("vm166.jinr.ru", database="icinga2")
    data = client.query("SELECT value FROM check_openvz_vm_perf WHERE metric =~ /mem_kb_.*/ GROUP BY metric, hostname ORDER BY time")
    pp = data.items()
    for k, v in pp:
        tags = {"service": "openvz_perf"}
        tags.update(k[1])
        tags['metric'] = tags['metric'].replace('_kb_', '_b_')
        pprint(tags)
        pack = lambda x: {'time': x['time'], 'fields': {'value': x['value']} }
        points = imap(pack, v)
        client.write({"measurement": "check_openvz_vm_perf", "tags": tags, "points": points}, params={'db': 'icinga2'})
    print 'done'

if __name__ == "__main__":
    main()