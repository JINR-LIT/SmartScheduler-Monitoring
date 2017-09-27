#!/usr/bin/env python
import re
from collections import defaultdict
from decimal import Decimal


def make_cpu_dict(cpu_list):
    return dict(
        (id, {'id': id, 'uptime_delta': uptime, 'cpu_percent': cpu, 'alloc_cpu': acpu}) for id, uptime, cpu, acpu in
        cpu_list)


def make_mem_dict(mem_list):
    return dict((id, {'id': id, 'mem_used': used, 'mem_total': total, 'mem_percent': mem}) for id, used, total, mem in
                mem_list)


def merge_info_dicts(a, b):
    r = defaultdict(dict, a)
    for k, v in b.iteritems():
        r[k].update(v)
    return r


def parse_free(free_output):
    expected_free = ['total', 'used', 'free']
    lines = free_output.split('\n')
    free = [re.split(" +", line.strip()) for line in lines]
    if free[0][:3] != expected_free:
        raise Exception("Unexpected free headers", free[0])
    if free[1][0] != "Mem:":
        raise Exception("Unexpected free line header", free[1][0])
    return free[1][1:3]


def get_mem(free):
    total, used = free
    return total, used, Decimal(used) * 100 / Decimal(total)
