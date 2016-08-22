#!/usr/bin/python2 -u
import argparse
import errno
import snmp_passpersist as snmp
import syslog
import sys
import os
import time
from probe_openvz import get_cpu, get_mem_info

pp = None

def update():
    global pp
    pp.add_int('0.0.0', int(time.time()))
    try:
        cpuinfo = list(get_cpu())
        pp.add_int('1.0', len(cpuinfo))
        for i in range(len(cpuinfo)):
            id, uptime, cpu = cpuinfo[i]
            pp.add_int('1.1.{0}.0'.format(i), id)
            pp.add_int('1.1.{0}.1'.format(i), uptime)
            pp.add_int('1.1.{0}.2'.format(i), int(cpu * 100))
            pp.add_int('1.1.{0}.3'.format(i), int(time.time()))
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, 'SMNP PassPersist OpenVZ CPU: error {0}'.format(e))
    try:
        meminfo = get_mem_info()
        meminfo = [[row[x] for x in ['ctid', 'mem_used', 'mem_percent', 'mem_total']] for row in meminfo.values()]
        pp.add_int('2.0', len(meminfo))
        for i in range(len(meminfo)):
            id, used, mem, total = meminfo[i]
            pp.add_int('2.1.{0}.0'.format(i), id)
            pp.add_int('2.1.{0}.1'.format(i), used)
            pp.add_int('2.1.{0}.2'.format(i), int(mem * 100))
            pp.add_int('2.1.{0}.3'.format(i), total)
            pp.add_int('2.1.{0}.4'.format(i), int(time.time()))
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, 'SMNP PassPersist OpenVZ Memory: error {0}'.format(e))

def main():
    global pp
    unbuffered = os.fdopen(sys.stdout.fileno(), 'w', 0)
    sys.stdout.close()
    sys.stdout = unbuffered

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--oid', dest='oid_base', default='.1.3.6.1.4.1.8072.1.3.7')
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

if __name__ == "__main__":
    main()