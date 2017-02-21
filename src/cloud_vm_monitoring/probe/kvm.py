#!/usr/bin/env python

import sh
import re
from decimal import Decimal

from cloud_vm_monitoring.probe.util import make_cpu_dict, make_mem_dict, merge_info_dicts

expected_header = ['ID', 'CPU', 'MEM', 'TOTAL', 'UPTIME']


def get_cpu(kvm_pseudo_vestat):
    lines = kvm_pseudo_vestat.split('\n')
    vestat = [re.split(" +", line.strip()) for line in lines][:-1]
    if vestat[0] != expected_header:
        raise Exception("Unexpected kvm data header")
    for row in vestat[1:]:
        id = int(row[0])
        uptime = row[4]
        cpu = Decimal(row[1]) * 100
        yield (id, uptime, cpu)


def get_cpu_info():
    return make_cpu_dict(get_cpu(sh.sh("/opt/openvz-snmp-extend/src/cloud_vm_monitoring/probe_kvm").stdout))


def get_mem(kvm_pseudo_vestat):
    lines = kvm_pseudo_vestat.split('\n')
    vestat = [re.split(" +", line.strip()) for line in lines][:-1]
    if vestat[0] != expected_header:
        raise Exception("Unexpected kvm data header")
    for row in vestat[1:]:
        id = int(row[0])
        total = row[3]
        used = row[2]
        mem = Decimal(used)/Decimal(total) * 100
        yield (id, used, total, mem)


def get_mem_info():
    return make_mem_dict(get_mem(sh.sh("/opt/openvz-snmp-extend/src/cloud_vm_monitoring/probe_kvm").stdout))


def main():
    from socket import gethostname
    hostname = gethostname()
    vm_dict = merge_info_dicts(get_cpu_info(), get_mem_info())
    for id, vm in vm_dict.items():
        cpu = vm.get('cpu_percent')
        mem = vm.get('mem_used')
        print "HOST={0} USEDCPU={1} USEDMEMORY={2} NAME={3}".format(
            hostname, cpu, mem, id)

if __name__ == "__main__":
    main()
