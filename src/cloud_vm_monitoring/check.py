#!/usr/bin/python2
from decimal import Decimal

import easysnmp
import pynag


def walk_cpu(session, oid):
    n = int(session.get("{oid}.1.0".format(oid=oid)).value)
    for i in range(n):
        id, uptime, cpu = (x.value for x in session.walk("{oid}.1.1.{i}".format(oid=oid, i=i)))
        yield (id, Decimal(uptime), Decimal(cpu))


def walk_mem(session, oid):
    n = int(session.get("{oid}.2.0".format(oid=oid)).value)
    for i in range(n):
        id, used, percent, total = (x.value for x in session.walk("{oid}.2.1.{i}".format(oid=oid, i=i)))
        yield (id, Decimal(used), Decimal(percent), Decimal(total))


def get_host_cpu(session, oid):
    count, percent = session.get("{oid}.1.2.0".format(oid=oid)).value, session.get("{oid}.1.2.1".format(oid=oid)).value
    return count, Decimal(percent)


def get_host_mem(session, oid):
    used, percent, total = session.get("{oid}.2.2.1".format(oid=oid)).value, \
                           session.get("{oid}.2.2.2".format(oid=oid)).value, \
                           session.get("{oid}.2.2.3".format(oid=oid)).value
    return used, Decimal(percent), total


def add_cpu(ph, metrics):
    sumcpu = Decimal(0)
    cpucount = 0
    for id, uptime, percent in metrics:
        if uptime > 0:
            sumcpu += percent
            cpucount += 1
        ph.add_metric('cpu_{0}'.format(id), percent.quantize(Decimal('.01')),
                      ph.options.cpu_w, ph.options.cpu_c, uom='%', min=0)
        ph.add_metric('dt_{0}'.format(id), (uptime / Decimal('1000')).quantize(Decimal('.01')),
                      ph.options.dt_w, ph.options.dt_c, uom='s')


def add_mem(ph, metrics):
    summem = Decimal(0)
    memcount = 0
    sumb = 0
    for id, used, percent, total in metrics:
        summem += percent
        sumb += used
        memcount += 1
        ph.add_metric('mem_{0}'.format(id), percent.quantize(Decimal('.01')),
                      ph.options.mem_w, ph.options.mem_c, uom='%', min=0, max=100)
        ph.add_metric('mem_b_{0}'.format(id), used,
                      ph.options.b_w, ph.options.b_c, uom='B', min=0, max=total)
    if summem:
        ph.add_summary("avg vm memory: {avg}%".format(avg=(summem / memcount).quantize(Decimal('.01'))))
        ph.add_summary("total vm memory used: {sumb} B".format(sumb=sumb))


def add_host_cpu(ph, count, percent):
    ph.add_metric('host_cpu_count', count)
    ph.add_metric('host_cpu_load', percent.quantize(Decimal('.01')), min=0, max=100)
    ph.add_summary("Host CPU: {0}%".format(percent.quantize(Decimal('.01'))))


def add_host_mem(ph, used, percent, total):
    ph.add_metric('host_mem_used_bytes', used, uom='B', min=0, max=total)
    ph.add_metric('host_mem_used_percent', percent, uom='%', min=0, max=100)
    ph.add_metric('host_mem_total_bytes', total, uom='B')
    ph.add_summary("Host Memory: {0}%".format(percent.quantize(Decimal('.01'))))


def check(default_oid):
    ph = pynag.Plugins.PluginHelper()
    og_snmp = ph.parser.add_option_group("SNMP")
    og_snmp.add_option("-H", "--host", help="Hostname or ip address", dest="host", default="localhost")
    og_snmp.add_option("--oid", help="oid root for VM data", dest="oid", default=default_oid)
    og_snmp.add_option("-C", "--community", dest="community", default="public")
    og_snmp.add_option("-V", "--version", dest="version", default=2)

    og_cpu = ph.parser.add_option_group("CPU")
    og_cpu.add_option("--cpu-crit", help="vm cpu load in %", dest='cpu_c', default="")
    og_cpu.add_option("--cpu-warn", dest='cpu_w', default="")
    og_cpu.add_option("--cpu-dt-crit", help="uptime interval over which cpu was calculated",
                      dest='dt_c', default="")
    og_cpu.add_option("--cpu-dt-warn", dest='dt_w', default="")

    og_mem = ph.parser.add_option_group("Memory")
    og_mem.add_option("--mem-crit", help="used memory in %", dest='mem_c', default=":99")
    og_mem.add_option("--mem-warn", dest='mem_w', default=":95")
    og_mem.add_option("--mem-b-crit", help="used memory in bytes", dest='b_c', default='')
    og_mem.add_option("--mem-b-warn", dest='b_w', default='')

    ph.parse_arguments()
    session = easysnmp.Session(hostname=ph.options.host, community=ph.options.community,
                               version=int(ph.options.version))

    add_cpu(ph, walk_cpu(session, ph.options.oid))
    add_mem(ph, walk_mem(session, ph.options.oid))
    add_host_cpu(ph, *get_host_cpu(session, ph.options.oid))
    add_host_mem(ph, *get_host_mem(session, ph.options.oid))


    ph.add_metric('timestamp', session.get("{oid}.0.0.0".format(oid=ph.options.oid)).value)
    ph.check_all_metrics()
    ph.exit()


def check_openvz():
    check(".1.3.6.1.4.1.8072.1.3.7")


def check_kvm():
    check(".1.3.6.1.4.1.8072.1.3.8")


if __name__ == "__main__":
    check_openvz()
