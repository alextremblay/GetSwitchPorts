import pytest

from GetSwitchPorts import snmp

SNMP_SRV_ADDR = '127.0.0.1'
SNMP_SRV_PORT = '10000'
IFTABLE_OID = '.1.3.6.1.2.1.2.2'
IFXTABLE_OID = '.1.3.6.1.2.1.31.1.1'


@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    result = sock.connect_ex((SNMP_SRV_ADDR, int(SNMP_SRV_PORT)))
    assert result == 0, "SNMP test server does not appear to be running"


def test_snmptable_return_structure():
    '''snmptable return data should be a list of dicts containing info about 
    each row in the table'''
    iftable = snmp.snmptable('cisco-switch', SNMP_SRV_ADDR, SNMP_SRV_PORT,
                             IFTABLE_OID, 'ifIndex')
    assert type(iftable) is list
    assert type(iftable[0]) is dict
    assert type(iftable[0]['ifDescr']) is str
    assert iftable[0]['ifDescr'] == 'Vlan1'


def test_snmptable_wrong_oid():
    with pytest.raises(ChildProcessError):
        snmp.snmptable('cisco-chassis', SNMP_SRV_ADDR, SNMP_SRV_PORT,
                       'WRONG-MIB::Bogus-Table')


def test_snmptable_not_table():
    with pytest.raises(snmp.SNMPError) as excinfo:
        snmp.snmptable('cisco-chassis', SNMP_SRV_ADDR, SNMP_SRV_PORT,
                       'IF-MIB::ifEntry')
    assert 'could not identify IF-MIB::ifEntry as a table' in str(excinfo.value)


def test_snmptable_invalid_address():
    with pytest.raises(ValueError) as excinfo:
        snmp.snmptable('cisco-chassis', 'totally not an ip address',
                       SNMP_SRV_PORT, 'some-irelevant-oid')
    assert 'does not appear to be an IPv4 or IPv6 address' in str(excinfo.value)


def test_snmptable_timeout():
    with pytest.raises(snmp.SNMPError) as excinfo:
        snmp.snmptable('cisco-chassis', '10.0.0.1', SNMP_SRV_PORT,
                       'IF-MIB::ifTable', timeout=1)
    assert 'Timeout' in str(excinfo.value)
