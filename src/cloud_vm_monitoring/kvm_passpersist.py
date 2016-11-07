#!/usr/bin/python2 -u
import snmp_passpersist as snmp
import syslog
import sys
import os
from probe_kvm import get_cpu, get_mem_info

unbuffered = os.fdopen(sys.stdout.fileno(), 'w', 0)
sys.stdout.close()
sys.stdout = unbuffered

pp = snmp.PassPersist(".1.3.6.1.4.1.8072.1.3.8")

def update():
    try:
        cpuinfo= list(get_cpu())
        pp.add_int('1.0', len(cpuinfo))
        for i in range(len(cpuinfo)):
            id, uptime, cpu = cpuinfo[i]
            pp.add_int('1.1.{0}.0'.format(i), id)
            pp.add_int('1.1.{0}.1'.format(i), uptime)
            pp.add_int('1.1.{0}.2'.format(i), cpu) 
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, 'SMNP PassPersist KVM CPU: error {0}'.format(e))
    try:
        meminfo = list(get_mem_info())
        pp.add_int('2.0', len(meminfo))
        for i in range(len(meminfo)):
            id, used, total, mem = meminfo[i]
            pp.add_int('2.1.{0}.0'.format(i), id)
            pp.add_int('2.1.{0}.1'.format(i), used)
            pp.add_int('2.1.{0}.2'.format(i), mem)
            pp.add_int('2.1.{0}.3'.format(i), total)
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, 'SMNP PassPersist KVM Memory: error {0}'.format(e))

def main():
    syslog.openlog(sys.argv[0], syslog.LOG_PID)
    pp.start(update, 10)

if __name__ == "__main__":
    main()
