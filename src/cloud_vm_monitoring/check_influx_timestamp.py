#!/usr/bin/env python 
import pynag
from influxdb import InfluxDBClient


def get_metrics_for_host(client, host=None, limit=3):
    host_filter = "" if host is None else "AND hostname = '{}' ".format(host)
    static_metrics = "^(dt_.*|mem_.*|host_mem_.*|host_cpu_alloc|host_cpu_count|num_cpu_.*)$"
    query = """SELECT value FROM /^check_(openvz|kvm)_vm_perf$/ 
               WHERE metric !~ /{static_metrics}/ 
               {host_filter} AND time > now() - 1d 
               GROUP BY hostname, metric ORDER BY time DESC LIMIT {limit};
               """.format(static_metrics=static_metrics, limit=limit, host_filter=host_filter)
    result = client.query(query)
    for key, values in result.items():
        tags = '|'.join(key[1].values())
        yield tags, [temp['value'] for temp in values]


def main():
    ph = pynag.Plugins.PluginHelper()
    ph.parser.add_option("--host", default=None)
    ph.parser.add_option("--dbhost", default="localhost")
    ph.parser.add_option("--limit", default=15, type='int')
    ph.parser.add_option("--ssl", action="store_true", default="False")
    ph.parser.add_option("--no-ssl", action="store_false", dest="ssl")
    ph.parser.add_option("--username")
    ph.parser.add_option("--password")
    ph.parse_arguments()
    ph.add_summary(str(ph.options.host))
    client = InfluxDBClient(ph.options.dbhost, 8086, ph.options.username, ph.options.password, 'icinga2', ph.options.ssl)
    metrics = get_metrics_for_host(client, ph.options.host, ph.options.limit)
    for tags, values in metrics:
        if len(set(values)) == 1 and len(values) == ph.options.limit:
            ph.add_status('critical')
            ph.add_summary('{} is stuck'.format(tags))
            ph.add_summary(str(values))
        else:
            ph.add_status('ok')
    ph.check_all_metrics()
    ph.exit()


if __name__ == "__main__":
    main()
