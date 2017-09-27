USE icinga2
CREATE DATABASE mem_old
SELECT * INTO mem_old..mem_b FROM check_kvm_vm_perf WHERE metric =~ /mem_b_.*/ AND hostname="" GROUP BY *
// stop monitoring here or earlier
DROP SERIES FROM check_kvm_vm_perf WHERE metric =~ /mem_b_.*/ AND hostname=""
SELECT 1024*value INTO check_kvm_vm_perf FROM mem_old..mem_b WHERE hostname="" GROUP BY *
DROP SERIES FROM mem_old..mem_b WHERE hostname=""
// while the data is copied, you can update and resume monitoring
DROP DATABASE mem_old
