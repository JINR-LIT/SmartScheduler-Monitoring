#!/bin/env python2
from os import listdir
from os.path import join, isdir
from struct import pack, unpack

from whisper import __readHeader, pointSize, pointFormat


# !!!!!!!!!!!!!!!!!!!!!!!!!
# ! stop monitoring first !
# !!!!!!!!!!!!!!!!!!!!!!!!!

def do_scale(fname):
    with open(fname, 'r+b') as fh:
        header = __readHeader(fh)
        for archive in header['archives']:
            assert pointSize * archive['points'] == archive['size']
            fh.seek(archive['offset'])
            for n in range(archive['points']):
                time, value = unpack(pointFormat, fh.read(pointSize))
                fh.seek(-pointSize, 1)
                fh.write(pack(pointFormat, time, value * 1024))


data_dir = '/var/lib/carbon/whisper/icinga2'
virt = 'kvm'

for host in listdir(data_dir):
    print "checking host " + host
    service_dir = join(data_dir, host, 'services/' + virt + '_perf')
    if not isdir(service_dir):
        print "no cloud performace metrics"
        continue
    print "cloud metrics found, scaling"
    metricdir = join(service_dir, 'check_' + virt + '_vm_perf/perfdata')
    for metric in listdir(metricdir):
        if metric.startswith('mem_b'):
            fname = join(metricdir, metric, 'value.wsp')
            do_scale(fname)
