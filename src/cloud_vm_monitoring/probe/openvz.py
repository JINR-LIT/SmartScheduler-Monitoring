#!/usr/bin/env python

import json
import sh
import re
from decimal import Decimal

from cloud_vm_monitoring.probe.util import make_cpu_dict, merge_info_dicts


def read_vestat(vestat_file='/proc/vz/vestat'):
    with open(vestat_file) as fin:
        return fin.readlines()


def parse_vestat(vestat_lines):
    expected_vestat = ['VEID', 'user', 'nice', 'system', 'uptime', 'idle', 'strv', 'uptime', 'used', 'maxlat', 'totlat',
                       'numsched']
    expected_version = 'Version: 2.2'
    got_version = vestat_lines[0].strip()
    if got_version != expected_version:
        raise Exception("Unexpected vestat version", got_version)
    vestat = [re.split(" +", line.strip()) for line in vestat_lines[1:]]
    if vestat[0] != expected_vestat:
        raise Exception("Unexpected vestat headers", vestat[0])
    return vestat[1:]

last_vestat = {}


def get_cpu(vestat):
    global last_vestat
    next_vestat = {}
    for row in vestat:
        id = int(row[0])
        next_vestat[id] = row[1:]
        if id in last_vestat:
            diff = [int(row[i])-int(last_vestat[id][i-1]) for i in range(1, len(row))]
            user, nice, system, uptime = diff[:4]
            if uptime>0:
                cpu = (user + nice + system) / Decimal(uptime) * 100
            else:
                cpu = Decimal(0)
            yield (id, uptime, cpu)
    last_vestat = next_vestat


def get_cpu_info():
    return make_cpu_dict(get_cpu(parse_vestat(read_vestat())))


def read_free(id):
    return sh.vzctl("exec", id, "free", "-b").stdout


def parse_free(free_output):
    expected_free = ['total', 'used', 'free', 'shared', 'buffers', 'cached']
    lines = free_output.split('\n')
    free = [re.split(" +", line.strip()) for line in lines]
    if free[0] != expected_free:
        raise Exception("Unexpected free headers", free[0])
    if free[1][0] != "Mem:":
        raise Exception("Unexpected free line header", free[1][0])
    return free[1][1:3]


def get_mem(free):
    total, used = free
    return total, used, Decimal(used)/Decimal(total) * 100


def get_vm_list():
    return json.loads(sh.vzlist('-j').stdout)


def update_mem_info(vm):
    vm['id'] = vm['ctid']
    if vm['status'] != 'stopped':
        total, used, mem = get_mem(parse_free(read_free(vm['ctid'])))
        vm.update({'mem_total': total, 'mem_used': used, 'mem_percent': mem})
    return vm


def get_mem_info():
    return dict((vm['ctid'], update_mem_info(vm)) for vm in get_vm_list())


def main():
    from socket import gethostname
    from time import sleep
    hostname = gethostname()
    get_cpu_info()
    sleep(2)
    vm_dict = merge_info_dicts(get_mem_info(), get_cpu_info())
    for id, vm in vm_dict.items():
        state = vm.get('status')
        cpu = vm.get('cpu_percent')
        mem = vm.get('mem_used')
        print "HOST={0} STATE={1} USEDCPU={2} USEDMEMORY={3} NAME={4}".format(
            hostname, state, cpu, mem, id)

if __name__ == "__main__":
    main()