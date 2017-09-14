#!/usr/bin/env python
import time
from StringIO import StringIO
import pytest
import os

from libvirt import libvirtError

from cloud_vm_monitoring.probe.kvm import get_cpu, get_mem, get_mem_info, get_cpu_info, main, reset_global


def test_get_cpu():
    assert list(get_cpu('test:///default')) == []
    time.sleep(1)
    cpu = list(get_cpu('test:///default'))
    assert len(cpu) == 1
    assert cpu[0] == pytest.approx(('test', 1.0, 100, 2), 0.01)
    reset_global()


def test_get_cpu_fractional():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    with pytest.raises(libvirtError) as exc_info:
        list(get_cpu('test:///{}/libvirt_test_fractional.xml'.format(test_dir)))
    assert exc_info.value.message == 'XML error: maximum vcpus count must be an integer'


def test_cpu_info():
    assert get_cpu_info('test:///default') == {}
    time.sleep(2)
    cpu = get_cpu_info('test:///default')
    assert type(cpu) == dict
    assert cpu.keys() == ['test']
    assert cpu['test'] == pytest.approx({'id': 'test', 'uptime_delta': 1, 'cpu_percent': 100, 'alloc_cpu': 2}, 0.01)
    reset_global()


def test_get_mem():
    assert list(get_mem('test:///default')) == [('test', 2147483648L, 8589934592L, 25)]


def test_mem_info():
    assert get_mem_info('test:///default') == {'test': {'id': 'test', 'mem_percent': 25.0, 'mem_total': 8589934592L,
                                                        'mem_used': 2147483648L}}


def test_main(mocker):
    mocker.patch('socket.gethostname', return_value='example.com')
    out = mocker.patch('sys.stdout', new_callable=StringIO)
    main('test:///default')
    assert out.getvalue() == "HOST=example.com USEDCPU=100.0 USEDMEMORY=2147483648 NAME=test\n"
