#!/usr/bin/env python

from collections import defaultdict


def make_cpu_dict(cpu_list):
    return dict((id, {'id': id, 'uptime_delta': uptime, 'cpu_percent': cpu}) for id, uptime, cpu in
                cpu_list)


def make_mem_dict(mem_list):
    return dict((id, {'id': id, 'mem_used': used, 'mem_total': total, 'mem_percent': mem}) for id, used, total, mem in
                mem_list)


def merge_info_dicts(a, b):
    r = defaultdict(dict, a)
    for k, v in b.iteritems():
        r[k].update(v)
    return r
