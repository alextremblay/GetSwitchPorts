from GetSwitchPorts import snmp
# import pytest


def test_snmptable():
    tempvar = snmp.snmptable('recorded/cisco-chassis', '127.0.0.1:10000',
                   '.1.3.6.1.2.1.31.1.1')
    print tempvar[0]
