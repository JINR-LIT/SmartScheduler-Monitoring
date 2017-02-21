#!/usr/bin/env python

from cloud_vm_monitoring.probe.util import make_mem_dict, make_cpu_dict, merge_info_dicts


def test_make_cpu_dict():
    assert make_cpu_dict([(123, 2, 50), (124, 4, 20)]) == \
           {123: {'id': 123, 'uptime_delta': 2, 'cpu_percent': 50},
            124: {'id': 124, 'uptime_delta': 4, 'cpu_percent': 20}}


def test_make_mem_dict():
    assert make_mem_dict([(123, 256, 512, 50), (124, 128, 1024, 12.5)]) == \
           {123: {'id': 123, 'mem_used': 256, 'mem_total': 512, 'mem_percent': 50},
            124: {'id': 124, 'mem_used': 128, 'mem_total': 1024, 'mem_percent': 12.5}}


def test_merge_info_dicts():
    assert merge_info_dicts({'a': {}}, {'b': {}}) == {'a': {}, 'b': {}}
    assert merge_info_dicts({'a': {'x': 'y'}}, {'a': {'a': 'b'}}) == {'a': {'x': 'y', 'a': 'b'}}
    assert merge_info_dicts({'a': {'x': 'y'}}, {'b': {'a': 'b'}}) == {'a': {'x': 'y'}, 'b': {'a': 'b'}}
    assert merge_info_dicts({1: {'a': 10}, 2: {'a': 20}}, {1: {'b': 'x'}, 3: {'c': 'y'}}) == \
           {1: {'a': 10, 'b': 'x'}, 2: {'a': 20}, 3: {'c': 'y'}}