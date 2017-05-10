from GetSwitchPorts import snmp
# import pytest


def test_snmptable():
    tempvar = snmp.snmptable('recorded/cisco-chassis', '127.0.0.1:10000',
                             'IF-MIB::ifTable', 'ifIndex')
    tempvar2 =  snmp.snmptable('recorded/cisco-chassis', '127.0.0.1:10000',
                               'IF-MIB::ifXTable', 'index')
    print tempvar[10]['index']
    print tempvar2[10]['index']
    print tempvar[0]
    print tempvar2[0]

