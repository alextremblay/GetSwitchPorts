import pytest

from GetSwitchPorts import snmp

SNMP_SRV_ADDR = '127.0.0.1'
SNMP_SRV_PORT = '10000'
IFTABLE_OID = '.1.3.6.1.2.1.2.2'
IFXTABLE_OID = '.1.3.6.1.2.1.31.1.1'


@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test():
    '''We're using snmpsim to simulate various target devices for our tests. 
    Before we do anything, we should probably make sure it's actually running'''
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    result = sock.connect_ex((SNMP_SRV_ADDR, int(SNMP_SRV_PORT)))
    assert result == 0, "SNMP test server does not appear to be running"

snmp_commands = [
    snmp.snmpget,
    snmp.snmpgetbulk,
    snmp.snmpwalk,
    snmp.snmptable,
]

def test_snmp_invalid_address():
    '''all snmp commands should implement the check_invalid_address function'''
    for command in snmp_commands:
        with pytest.raises(snmp.SNMPError) as excinfo:
            command('public', 'invalid-hostname', 'some-irelevant-oid')
        assert 'does not appear to be a valid' in str(excinfo.value)


def test_snmp_timeout():
    '''all snmp commands should implement the check_timeout function'''
    for command in snmp_commands:
        with pytest.raises(snmp.SNMPError) as excinfo:
            command('cisco-chassis', '10.0.0.1', 'IF-MIB::ifTable', timeout=1)
        assert 'Timeout' in str(excinfo.value)


def test_snmptable_return_structure():
    '''snmptable return data should be a list of dicts containing info about 
    each row in the table'''
    iftable = snmp.snmptable('cisco-switch', SNMP_SRV_ADDR, IFTABLE_OID,
                             SNMP_SRV_PORT, sortkey='ifIndex')
    assert type(iftable) is list
    assert type(iftable[0]) is dict
    assert type(iftable[0]['ifDescr']) is str
    assert iftable[0]['ifDescr'] == 'Vlan1'


def test_snmptable_wrong_oid():
    with pytest.raises(ChildProcessError):
        snmp.snmptable('cisco-chassis', SNMP_SRV_ADDR,'WRONG-MIB::Bogus-Table',
                       SNMP_SRV_PORT)


def test_snmptable_not_table():
    with pytest.raises(snmp.SNMPError) as excinfo:
        snmp.snmptable('cisco-chassis', SNMP_SRV_ADDR, 'IF-MIB::ifEntry',
                       SNMP_SRV_PORT)
    assert 'could not identify IF-MIB::ifEntry as a table' in str(excinfo.value)


def test_snmpget_return_structure():
    result = snmp.snmpget('cisco-switch', SNMP_SRV_ADDR,
                          '.1.3.6.1.2.1.1.1.0', SNMP_SRV_PORT)
    assert 'Cisco IOS Software' in result
    assert type(result) is str


def test_snmpget_no_such_instance():
    result = snmp.snmpget('cisco-switch', SNMP_SRV_ADDR, 'SNMPv2-MIB::sysName',
                     SNMP_SRV_PORT)
    assert result is None

def test_snmpgetbulk_return_structure():
    oids = ['IF-MIB::ifTable.1.1.1', 'IF-MIB::ifTable.1.2.1',
            'IF-MIB::ifTable.1.3.1']
    result = snmp.snmpgetbulk('cisco-switch', SNMP_SRV_ADDR, oids,
                          SNMP_SRV_PORT)
    assert type(result) is list
    assert len(result) == len(oids)
    assert type(result[0]) is tuple
    assert type(result[0][0]) is str
    assert type(result[0][1]) is str
    assert result[1][0] == '.1.3.6.1.2.1.2.2.1.2.1'
    assert result[1][1] == 'Vlan1'


def test_snmpgetbulk_return_contains_no_such_instance():
    oids = ['IF-MIB::ifTable.1.1.1', 'IF-MIB::ifTable.1.2.1',
            'IF-MIB::ifTable.1.3']
    result = snmp.snmpgetbulk('cisco-switch', SNMP_SRV_ADDR, oids,
                          SNMP_SRV_PORT)
    assert result[2][0] == '.1.3.6.1.2.1.2.2.1.3'
    assert result[2][1] is None

def test_snmpwalk_return_structure():
    result = snmp.snmpwalk('cisco-switch', SNMP_SRV_ADDR, 'IF-MIB::ifTable',
                           SNMP_SRV_PORT)
    assert type(result) is list
    assert type(result[0]) is tuple
    assert type(result[0][0]) is str and type(result[0][1]) is str
    assert result[0][0] == '.1.3.6.1.2.1.2.2.1.1.1'
    assert result[0][1] == '1'