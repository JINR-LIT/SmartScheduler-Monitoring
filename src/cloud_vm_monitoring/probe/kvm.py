#!/usr/bin/env python

import time

import libvirt

from cloud_vm_monitoring.probe.util import make_cpu_dict, make_mem_dict, merge_info_dicts

previous = {}


# clean up between unittests
def reset_global():
    global previous
    previous = {}


def get_cpu(uri="qemu:///system"):
    global previous
    conn = libvirt.openReadOnly(uri)
    domains = conn.listDomainsID()
    last_time, record = previous.get(uri, (0, {}))
    now, new_record = time.time(), {}
    interval = now - last_time
    for id in domains:
        domain = conn.lookupByID(id)
        state, max_memory, memory, nb_virt_cpu, cpu_time = domain.info()
        new_record[id] = cpu_time
        if id in record:
            last_cpu_time = record[id]
            usage = cpu_time - last_cpu_time
            if usage > 0 and interval > 0:
                load = usage * 1e-9 / interval * 100
            else:
                load = 0
            vm_id = domain.name()
            vm_id = vm_id[4:] if vm_id.startswith('one-') else vm_id
            yield vm_id, interval, load, nb_virt_cpu
    previous[uri] = (now, new_record)


def get_cpu_info(uri="qemu:///system"):
    return make_cpu_dict(get_cpu(uri))


def get_mem(uri="qemu:///system"):
    conn = libvirt.openReadOnly(uri)
    domains = conn.listDomainsID()
    for id in domains:
        domain = conn.lookupByID(id)
        state, max_memory, memory, nb_virt_cpu, cpu_time = domain.info()
        vm_id = domain.name()
        vm_id = vm_id[4:] if vm_id.startswith('one-') else vm_id
        yield vm_id, memory * 1024, max_memory * 1024, memory * 100.0 / max_memory


def get_mem_info(uri="qemu:///system"):
    return make_mem_dict(get_mem(uri))


def main(uri="qemu:///system"):
    from socket import gethostname
    hostname = gethostname()
    get_cpu_info(uri)
    time.sleep(2)
    vm_dict = merge_info_dicts(get_cpu_info(uri), get_mem_info(uri))
    for id, vm in vm_dict.items():
        cpu = vm.get('cpu_percent')
        mem = vm.get('mem_used')
        print "HOST={0} USEDCPU={1:.1f} USEDMEMORY={2} NAME={3}".format(
            hostname, cpu, mem, id)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        uri = sys.argv[1]
    else:
        uri = "qemu:///system"
    main(uri)
