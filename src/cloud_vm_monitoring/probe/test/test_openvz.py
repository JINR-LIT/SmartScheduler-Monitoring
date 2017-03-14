#!/usr/bin/env python
from StringIO import StringIO
from collections import namedtuple
from decimal import Decimal
from functools import partial

import pytest
from mock import mock_open, patch

from cloud_vm_monitoring.probe.openvz import parse_vestat, get_cpu, get_mem_info, get_cpu_info, main, reset_global

vestat1 = """\
Version: 2.2
VEID                 user                 nice               system               uptime                 idle                 strv               uptime                 used               maxlat               totlat             numsched
1562             51549275               181854            912100476           2417366597     1452406508730671                    0     2417366627586771      963623204863434                    0                    0                    0
1563             65860345               180519           1139276245           2417372543     1211252784940736                    0     2417372574804311     1205028764195002                    0                    0                    0"""

vestat2 = """\
Version: 2.2
VEID                 user                 nice               system               uptime                 idle                 strv               uptime                 used               maxlat               totlat             numsched
1562             51549275               181854            912100476           2417380459     1452420370623343                    0     2417380489498886      963623204863434                    0                    0                    0
1563             65861152               180519           1139289300           2417386405     1211252785940584                    0     2417386436694681     1205042624087978                    0                    0                    0"""


def test_parse_vestat():
    assert parse_vestat(vestat1.split('\n')) == [['1562', '51549275', '181854', '912100476', '2417366597',
                                      '1452406508730671', '0', '2417366627586771', '963623204863434', '0', '0', '0'],
                                     ['1563', '65860345', '180519', '1139276245', '2417372543',
                                      '1211252784940736', '0', '2417372574804311', '1205028764195002', '0', '0', '0']]
    assert parse_vestat(vestat1.split('\n')[:2]) == []
    with pytest.raises(Exception):
        parse_vestat('asdf')
    assert parse_vestat(['Version: 2.2',
                         'VEID user nice system uptime idle strv uptime used maxlat totlat numsched']) == []
    with pytest.raises(Exception):
        parse_vestat(['Version: 2.1',
                      'VEID user nice system uptime idle strv uptime used maxlat totlat numsched'])
    with pytest.raises(Exception):
        parse_vestat(['Version: 2.2', 'VEID user nice'])


def test_get_cpu():
    assert list(get_cpu([['123', '0', '0', '0', '0']])) == []
    assert list(get_cpu([['123', '1', '0', '0', '2']])) == [(123, 2, Decimal(50))]
    reset_global()


def test_cpu_info():
    with patch("__builtin__.open", mock_open(read_data=vestat1)):
        assert get_cpu_info() == {}
    with patch("__builtin__.open", mock_open(read_data=vestat1)):
        assert get_cpu_info() == {1562: {'id': 1562, 'uptime_delta': 0, 'cpu_percent': 0},
                                  1563: {'id': 1563, 'uptime_delta': 0, 'cpu_percent': 0}}
    with patch("__builtin__.open", mock_open(read_data=vestat2)):
        assert get_cpu_info() == \
            {1562: {'id': 1562, 'uptime_delta': 80459 - 66597, 'cpu_percent': Decimal(0)},
             1563: {'id': 1563, 'uptime_delta': 86405 - 72543,
                    'cpu_percent': (1152 - 345 + 89300 - 76245) * 100 / Decimal(86405 - 72543)}}
    reset_global()

freemem = """\
total       used       free     shared    buffers     cached
Mem:    1073741824  497639424  576102400       4096          0  103686144
-/+ buffers/cache:  393953280  679788544
Swap:    134217728          0  134217728"""


def test_mem_info(mocker):
    mocker.patch('sh.vzctl', create=True,
                 return_value=namedtuple('sh_stub', ['stdout'])(stdout=freemem))
    mocker.patch('sh.vzlist', create=True,
                 return_value=namedtuple('sh_stub', ['stdout'])(stdout='[{"ctid": 123, "status": "running"}]'))
    assert get_mem_info() == {123: {'id': 123, 'ctid': 123, 'status': 'running',
                                    'mem_total':'1073741824', 'mem_used': '497639424',
                                    'mem_percent': Decimal('497639424') * 100 / Decimal('1073741824')}}


vestat3 = """\
Version: 2.2
VEID user nice system uptime idle strv uptime used maxlat totlat numsched
1562 0 0 0 0 1452406508730671 0 2417366627586771 963623204863434 0 0 0
1563 0 0 0 0 1211252784940736 0 2417372574804311 1205028764195002 0 0 0"""

vestat4 = """\
Version: 2.2
VEID user nice system uptime idle strv uptime used maxlat totlat numsched
1562 30 20 30 100 1452420370623343 0 2417380489498886 963623204863434 0 0 0
1563 100 100 100 200 1211252785940584 0 2417386436694681 1205042624087978 0 0 0"""


def test_main(mocker):
    mocker.patch('sh.vzctl', create=True,
                 return_value=namedtuple('sh_stub', ['stdout'])(stdout=freemem))
    mocker.patch('sh.vzlist', create=True,
                 return_value=namedtuple('sh_stub', ['stdout'])(stdout='[{"ctid": 1562, "status": "running"},'
                                                                '{"ctid": 1563, "status": "running"}]'))
    mocker.patch('socket.gethostname', return_value='example.com')
    mocker.patch('__builtin__.open', mock_open(read_data=vestat3))
    mocker.patch('time.sleep',
                 side_effect=partial(mocker.patch, '__builtin__.open', mock_open(read_data=vestat4)))
    out = mocker.patch('sys.stdout', new_callable=StringIO)
    main()
    assert out.getvalue() == "HOST=example.com STATE=running USEDCPU=80.0 USEDMEMORY=497639424 NAME=1562\n" \
                             "HOST=example.com STATE=running USEDCPU=150.0 USEDMEMORY=497639424 NAME=1563\n"
    reset_global()
