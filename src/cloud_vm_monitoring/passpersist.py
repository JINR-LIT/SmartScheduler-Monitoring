#!/usr/bin/python2 -u
import argparse
import errno
import os
import sys
import syslog
import time

import snmp_passpersist as snmp

from cloud_vm_monitoring.probe.kvm import get_cpu_info as get_kvm_cpu, get_mem_info as get_kvm_mem
from cloud_vm_monitoring.probe.openvz import get_cpu_info as get_openvz_cpu, get_mem_info as get_openvz_mem


def publish_cpu(pp, cpu_dict):
    pp.add_int('1.0', len(cpu_dict))
    ids = sorted(cpu_dict.keys())
    for i in range(len(ids)):
        vm = cpu_dict[ids[i]]
        pp.add_int('1.1.{0}.0'.format(i), ids[i])
        pp.add_int('1.1.{0}.1'.format(i), vm['uptime_delta'])
        pp.add_str('1.1.{0}.2'.format(i), vm['cpu_percent'])


def publish_mem(pp, mem_dict):
    pp.add_int('2.0', len(mem_dict))
    ids = sorted(mem_dict.keys())
    for i in range(len(ids)):
        vm = mem_dict[ids[i]]
        pp.add_int('2.1.{0}.0'.format(i), ids[i])
        pp.add_str('2.1.{0}.1'.format(i), vm['mem_used'])
        pp.add_str('2.1.{0}.2'.format(i), vm['mem_percent'])
        pp.add_str('2.1.{0}.3'.format(i), vm['mem_total'])


def update_factory(pp, cpu_getter, mem_getter):
    def update():
        pp.add_int('0.0.0', int(time.time()))
        try:
            publish_cpu(pp, cpu_getter())
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, 'SMNP PassPersist OpenVZ CPU: error {0}'.format(e))
        try:
            publish_mem(pp, mem_getter())
        except Exception as e:
            syslog.syslog(syslog.LOG_ERR, 'SMNP PassPersist OpenVZ Memory: error {0}'.format(e))
    return update


def passpersist(default_oid_base, cpu_getter, mem_getter):
    # respond to passpersist immediately
    # don't buffer or the protocol breaks
    unbuffered = os.fdopen(sys.stdout.fileno(), 'w', 0)
    sys.stdout.close()
    sys.stdout = unbuffered

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--oid', dest='oid_base', default=default_oid_base)
    parser.add_argument('-t', '--interval', dest='polling_interval', type=float, default=10)
    parser.add_argument('-r', '--retry', dest='max_retry', help='retry', type=int, default=10)
    args = parser.parse_args()

    syslog.openlog(sys.argv[0], syslog.LOG_PID)
    retry_timestamp = int(time.time())
    retry_counter = 0
    while retry_counter <= args.max_retry:
        try:
            syslog.syslog(syslog.LOG_INFO, "Starting Openvz perfdata monitoring")
            pp = snmp.PassPersist(args.oid_base)
            update = update_factory(pp, cpu_getter, mem_getter)
            pp.start(update, args.polling_interval)
        except KeyboardInterrupt:
            print "Exiting on user request."
            sys.exit(0)
        except IOError, e:
            if e.errno == errno.EPIPE:
                syslog.syslog(syslog.LOG_INFO, "Snmpd had close the pipe, exiting...")
                sys.exit(0)
            else:
                syslog.syslog(syslog.LOG_WARNING, "Updater thread has died: IOError: %s" % (e))
        except Exception, e:
            syslog.syslog(syslog.LOG_WARNING, "Main thread has died: %s: %s" % (e.__class__.__name__, e))
        else:
            syslog.syslog(syslog.LOG_WARNING, "Updater thread has died: %s" % (pp.error))

        syslog.syslog(syslog.LOG_WARNING, "Restarting monitoring in 5 sec...")
        time.sleep(5)

        # Errors frequency detection
        now = int(time.time())
        if now > retry_timestamp + 3600:  # If the previous error is older than 1H
            retry_counter = 1
        else:
            retry_counter += 1
        retry_timestamp = now
    syslog.syslog(syslog.LOG_ERR, "Giving up after {n} retries".format(n=retry_counter))
    sys.exit(1)


def openvz_passpersist():
    passpersist('.1.3.6.1.4.1.8072.1.3.7', get_openvz_cpu, get_openvz_mem)


def kvm_passpersist():
    passpersist('.1.3.6.1.4.1.8072.1.3.8', get_kvm_cpu, get_kvm_mem)

