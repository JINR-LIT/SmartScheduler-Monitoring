#!/usr/bin/python2
import json
import sh
import re
from socket import gethostname
from decimal import Decimal
from time import sleep

vestat_file = '/proc/vz/vestat'
expected_vestat = ['VEID', 'user', 'nice', 'system', 'uptime', 'idle', 'strv', 'uptime', 'used', 'maxlat', 'totlat', 'numsched']
last_vestat = {}

def get_cpu():
    global last_vestat
    with open(vestat_file) as fin:
        vestat = [re.split(" +", line.strip()) for line in fin.readlines()[1:]]
    if vestat[0] != expected_vestat:
        raise Exception("Possible error parsing vestat data")
    next_vestat = {}
    for row in vestat[1:]:
        id = int(row[0])
        next_vestat[id] = row[1:]
        if id in last_vestat:
            diff = [int(row[i])-int(last_vestat[id][i-1]) for i in range(1, len(row))]
            user, nice, system, uptime = diff[:4]
            if uptime>0:
                cpu = (user + nice + system) / Decimal(uptime) * 100
            else:
                cpu = Decimal(0)
            yield (id, uptime, cpu)
    last_vestat = next_vestat

def get_mem(id):
    lines = sh.vzctl("exec", id, "free", "-b").stdout.split('\n')
    free = [re.split(" +", line.strip()) for line in lines]
    if free[1][0] != "Mem:":
        raise Exception("Possible error parsing free data")
    total, used = free[1][1:3]
    return total, used, Decimal(used)/Decimal(total) * 100

def get_vm_list():
    return json.loads(sh.vzlist('-j').stdout)

def get_mem_info():
    vms = get_vm_list()
    result = {}
    for vm in vms:
        id = vm['ctid']
        result[id] = vm
        if vm['status'] != 'stopped':
            total, used, mem = get_mem(id)
            result[id].update({'mem_total': total, 'mem_used': used, 'mem_percent': mem})
    return result

def get_all_info():
    result = get_mem_info()
    for id, uptime, cpu in get_cpu():
        res = result.get(id, {'ctid': id})
        res.update({'uptime_delta': uptime, 'cpu_percent': cpu})
        result[id] = res
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
        mem = vm.get('mem_used')
        print "HOST={0} DEPLOY_ID={1} STATE={2} USEDCPU={3} USEDMEMORY={4} NAME={5}".format(
            hostname, deploy, state, cpu, mem, id)

if __name__ == "__main__":
    main()