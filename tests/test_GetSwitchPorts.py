"""
For these tests, we will use a local snmpsim instance loaded up with snmprec 
files for a cisco chassis, a cisco switch, a nortel stack, and a nortel switch
"""
import pytest

from GetSwitchPorts import SwitchInfo

SNMP_SRV_ADDR = '127.0.0.1'
SNMP_SRV_PORT = 10000


def test_SwitchInfo_returns_None_on_invalid_address(capfd):
    """
    If the target switch's IP address / hostname is invalid, the call to 
    SwitchInfo should return None, and a message should be printed detailing 
    the problem
    """
    result = SwitchInfo('invalid-hostname')
    assert result is None
    capturedoutput = capfd.readouterr()[0]
    assert 'Invalid Address' in capturedoutput





def test_SwitchInfo_returns_None_when_target_offline(capfd):
    """
    If the target switch is offline, the call to SwitchInfo should return None, 
    and a message should be printed detailing the problem
    """
    non_existant_host = '127.99.99.99'
    result = SwitchInfo(non_existant_host, timeout=1)
    assert result is None
    capturedoutput = capfd.readouterr()[0]
    assert 'Unable to communicate' in capturedoutput
    assert str(non_existant_host) in capturedoutput


def test_SwitchInfo_returns_None_when_community_string_incorrect(capfd):
    """
    If the target switch's IP address / hostname is invalid, or if the device 
    is offline, or not responding to SNMP, the call to SwitchInfo should 
    return None, and a message should be printed detailing
    """
    result = SwitchInfo(SNMP_SRV_ADDR, SNMP_SRV_PORT,
                        'bogus_community_string', timeout=1)
    assert result is None
    capturedoutput = capfd.readouterr()[0]
    assert 'Unable to communicate' in capturedoutput
    assert str(SNMP_SRV_PORT) in capturedoutput


def test_SwitchInfo_return_structure():
    """
    If it works, the class instance returned should have a SwInfo dict in 
    it, and a porttable list of dicts
    """
    result = SwitchInfo(SNMP_SRV_ADDR, SNMP_SRV_PORT, 'cisco-switch')
    assert type(result) is list