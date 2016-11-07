#!/usr/bin/python2
import json
import sh
import re
from socket import gethostname
from decimal import Decimal
from time import sleep

expected_vestat = ['ID', 'CPU', 'MEM', 'TOTAL', 'UPTIME']
last_vestat = {}

def get_cpu():
    global last_vestat

    lines = sh.sh("/opt/openvz-snmp-extend/src/cloud_vm_monitoring/probe_kvm").stdout.split('\n')
    vestat = [re.split(" +", line.strip()) for line in lines][:-1]
    if vestat[0] != expected_vestat:
        raise Exception("Possible error parsing vestat data")
    next_vestat = {}
    for row in vestat[1:]:
        id = int(row[0])
        next_vestat[id] = row[1:]
        if id in last_vestat:
            uptime = next_vestat[id][3]
            if uptime>0:
                cpu = Decimal(next_vestat[id][0]) * 100
            else:
                cpu = Decimal(0)
            yield (id, uptime, cpu)
    last_vestat = next_vestat

def get_mem_info():
    global last_vestat

    lines = sh.sh("/opt/openvz-snmp-extend/src/cloud_vm_monitoring/probe_kvm").stdout.split('\n') 
    vestat = [re.split(" +", line.strip()) for line in lines][:-1]
    if vestat[0] != expected_vestat:
        raise Exception("Possible error parsing vestat data")
    next_vestat = {}
    for row in vestat[1:]:
        id = int(row[0])
        next_vestat[id] = row[1:]
	if id in last_vestat:
	   total =  next_vestat[id][2]
	   used = next_vestat[id][1]
	   mem = Decimal(used)/Decimal(total) * 100
           yield (id, used, total, mem)
    last_vestat = next_vestat

def get_all_info():
    result = get_mem_info()
    for id, uptime, cpu in get_cpu():
        result[id] = result.get(id, {'ctid': id}).update({'uptime_delta': uptime, 'cpu_percent': cpu})
    return result

def main():
    hostname = gethostname()
    get_all_info()
    sleep(2)
    info = get_all_info()
    for id, vm in info.items():
        if vm['status'] == 'stopped':
            continue
        deploy = 'one-{0}'.format(int(id)-1000)
        #TODO: fix state, vzctl status is more detailed than vzlist status
        state = {'running': 'a', 'user_suspended':'p'}[vm['status']]
        cpu = vm.get('cpu_percent')
        used = vm.get('mem_used')
        print "HOST={0} DEPLOY_ID={1} STATE={2} USEDCPU={3} USEDMEMORY={4} NAME={5}".format(
            hostname, deploy, state, cpu, mem, id)

if __name__ == "__main__":
    main()
