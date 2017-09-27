from sys import argv

from influxdb import InfluxDBClient


def scale(scale):
    def _scale(point):
        point['value'] = scale * point['value']
        return point

    return _scale


def pack(point):
    time = point.pop('time')
    point['value'] = float(point['value'])
    return {u'time': time, u'fields': point}


def main(dbhost):
    client = InfluxDBClient(dbhost, database="icinga2")
    counts = client.query("SELECT last(value) FROM /check_.*_vm_perf/ WHERE metric = 'host_cpu_count' GROUP BY *")
    for metadata, data in counts.items():
        count = float(list(data)[0]['last'])
        measurement, tags = metadata
        tags['metric'] = 'host_cpu_load'
        tag_cond = " AND ".join("{tag} = '{tagval}'".format(tag=tag, tagval=tagval) for tag, tagval in tags.items())
        print "working on data for hostname {}".format(tags['hostname'])
        percent = client.query("SELECT value "
                               "FROM {measurement} "
                               "WHERE {tag_cond} "
                               "GROUP BY *".format(measurement=measurement, tag_cond=tag_cond))
        tags['metric'] = 'host_cpu_load_cores'
        for series in percent:
            points = map(pack, map(scale(count), series))
            client.write({"measurement": measurement, "tags": tags, "points": points},
                         params={'db': 'icinga2'})
            print "written:", len(series)


if __name__ == "__main__":
    if len(argv) > 1:
        main(argv[1])
    else:
        main("localhost")
