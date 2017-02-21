#!/usr/bin/env python
import pytest

from StringIO import StringIO
from functools import partial
from collections import namedtuple
from decimal import Decimal
from mock import mock_open, patch

from cloud_vm_monitoring.probe.kvm import get_cpu, get_mem, get_mem_info, get_cpu_info, main

metrics_table = """\
ID CPU MEM TOTAL UPTIME
123 0.5 768 1024 10001
456 0.85 1024 2048 10000
"""


def test_get_cpu():
    assert list(get_cpu(metrics_table)) == [(123, '10001', 50), (456, '10000', 85)]
    with pytest.raises(Exception):
        list(get_cpu("bad"+metrics_table))


def test_cpu_info(mocker):
    mocker.patch('sh.sh', create=True,
                 return_value=namedtuple('sh_stub', ['stdout'])(stdout=metrics_table))
    assert get_cpu_info() == \
        {123: {'id': 123, 'uptime_delta': '10001', 'cpu_percent': 50},
         456: {'id': 456, 'uptime_delta': '10000', 'cpu_percent': 85}}


def test_get_mem():
    assert list(get_mem(metrics_table)) == [(123, '768', '1024', 75), (456, '1024', '2048', 50)]


def test_mem_info(mocker):
    mocker.patch('sh.sh', create=True,
                 return_value=namedtuple('sh_stub', ['stdout'])(stdout=metrics_table))
    assert get_mem_info() == {123: {'id': 123, 'mem_total': '1024', 'mem_used': '768', 'mem_percent': 75},
                              456: {'id': 456, 'mem_total': '2048', 'mem_used': '1024', 'mem_percent': 50}}


def test_main(mocker):
    mocker.patch('sh.sh', create=True,
                 return_value=namedtuple('sh_stub', ['stdout'])(stdout=metrics_table))
    mocker.patch('socket.gethostname', return_value='example.com')
    out = mocker.patch('sys.stdout', new_callable=StringIO)
    main()
    assert out.getvalue() == "HOST=example.com USEDCPU=85.00 USEDMEMORY=1024 NAME=456\n" \
                             "HOST=example.com USEDCPU=50.0 USEDMEMORY=768 NAME=123\n"
