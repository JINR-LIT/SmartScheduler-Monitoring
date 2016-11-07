#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='openvz-snmp-extend',
    use_scm_version=True,
    description="Nagios plugins to monitor openvz containers through snmp.",
    long_description=open('README.rst').read(),
    url='https://git.jinr.ru/kadivas/openvz-snmp-extend',
    author='',
    author_email='kadivas@jinr.ru',
    setup_requires=['setuptools_scm', 'setuptools>=12'],
    license="GPLv3 probably",
    classifiers=[], #see: https://pypi.python.org/pypi?%3Aaction=list_classifiers,
    keywords='nagios snmp openvz monitoring',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[],
    extras_require={
        'publish': ['sh>=1.07', 'snmp_passpersist'],
        'consume': ['easysnmp', 'pynag']
    },
    # include_package_data=True,
    entry_points={
        'console_scripts': [
            'check_openvz_vm_perf = cloud_vm_monitoring.check_openvz:main [consume]',
            'check_openvz_vm_cpu = cloud_vm_monitoring.check_openvz:check_cpu [consume]',
            'check_openvz_vm_mem = cloud_vm_monitoring.check_openvz:check_mem [consume]',
            'openvz_passpersist = cloud_vm_monitoring.openvz_passpersist:main [publish]',
            'check_kvm_vm_perf = cloud_vm_monitoring.check_kvm:main [consume]',
            'check_kvm_vm_cpu = cloud_vm_monitoring.check_kvm:check_cpu [consume]',
            'check_kvm_vm_mem = cloud_vm_monitoring.check_kvm:check_mem [consume]',
            'kvm_passpersist = cloud_vm_monitoring.kvm_passpersist:main [publish]'
        ]
    }
)
