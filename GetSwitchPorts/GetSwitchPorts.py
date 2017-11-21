#!/usr/bin/env python
"""
TODO: Module Docs
"""

# Internal module imports
from .snmp import snmpget, snmpgetbulk, snmptable, snmpwalk
from .snmp import validate_ip_address, run, PIPE, SNMPError

# Standard Library imports
import re  # RegEx module

# imports for type-hinting purposes
from typing import Union, Optional, Any,Type, List, Tuple, Dict

# External Package imports
import progressbar  # external package progressbar2

# specify some common OIDs
oids = {
    'sysName': '.1.3.6.1.2.1.1.5.0',
    'sysDescr': '.1.3.6.1.2.1.1.1.0',
    'ifNumber': '.1.3.6.1.2.1.2.1.0',
    'ifTable': '.1.3.6.1.2.1.2.2',
    'ifIndex': '.1.3.6.1.2.1.2.2.1.1',
    'ifDescr': '.1.3.6.1.2.1.2.2.1.2',
    'ifType': '.1.3.6.1.2.1.2.2.1.3',
    'ifPhysAddress': '.1.3.6.1.2.1.2.2.1.6',
    'ifXTable': '.1.3.6.1.2.1.31.1.1',
    'ifName': '.1.3.6.1.2.1.31.1.1.1.1',
    'ifAlias': '.1.3.6.1.2.1.31.1.1.1.18',
    'dot1qVlanStaticName': '.1.3.6.1.2.1.17.7.1.4.3.1.1',
    'Cisco': {
        'nativeVlan':
        '.1.3.6.1.4.1.9.9.68.1.2.2.1.2',  # VlanMembership_vmVlan from
        # CISCO-VLAN-MEMBERSHIP-MIB
        'vlanTable': ''
    },
    'Nortel': {
        'nativeVlan':
        '.1.3.6.1.4.1.2272.1.3.3.1.7',  # rcVlanPortDefaultVlanId from
        # RC-VLAN-MIB
        'vlanTable': ''
    },
}


class SwitchInfo(object):
    def __new__(cls,
                ip_address: str,
                port: Optional[int] = 161,
                community_string: Optional[str] = 'public',
                filter_type: Optional[str]=None,
                filter_keyword: Optional[str]=None,
                verbosity: Optional[int]=1,
                timeout: Optional[int]=3) -> Optional[object]:
        """

        This method runs during class instantiation, before an instance of the
        class is created. This method will run and check to see if the switch
        you're trying to make an instance for exists. If the switch is
        unresponsive, then prints an error and returns a false value instead of
        creating an instance. Otherwise, proceeds with Python's normal instance
        creation process (init process)

        :param ip_address: see SwitchInfo.__init__
        :param community_string: see SwitchInfo.__init__
        :param more: pass through positional arguments
        :return: an instance of this class, if the test succeeds. None otherwise
        """
        # Before creating a SwitchInfo instance for a given switch,
        # we should check to see if the target is valid
        try:
            ip_address = validate_ip_address(ip_address)
        except SNMPError as error:
            print(error)
            return None
        # Now we know the hostname / address is ok, let's try to connect and
        # verify that the device is online and our community string is valid.
        # For this test, we'll request an OID that should exist on just about
        # every SNMP server out there: sysDescr
        test_cmd_arg_list = ['snmpget',
                             '-v', '2c',
                             '-t', str(timeout),
                             '-c', community_string,
                             '{0}:{1}'.format(ip_address, port),
                             oids['sysDescr']]
        connection_test = run(
            test_cmd_arg_list, stdout=PIPE, stderr=PIPE)
        if connection_test.returncode is not 0:
            print("Unable to communicate with {0}:{1} over SNMP \n\
                  The error message we got was: {2}"
                  .format(ip_address, port, connection_test.stderr))
            return None
        # else:
        # If we get to this point, then all should be well. We will resume
        # instantiating our class.
        return super(SwitchInfo, cls).__new__(cls)

    def __init__(self,
                 ip_address: str,
                 port: Optional[int] = 161,
                 community_string: Optional[str] = 'public',
                 filter_type: Optional[str] = None,
                 filter_keyword: Optional[str] = None,
                 verbosity: Optional[int] = 1,
                 timeout: Optional[int] = 3):
        """

            This method will connect to a switch over SNMP and search the
            descriptions of all that device's ports for instances of a word of
            your choosing, or the word "UNUSED" if no search word is specified.

            :param ip_address: The IP of the device to poll
            :param community_string: the SNMPv2 read community string (read
            password) of the switch to poll
            :param filter_type: the port property to search by. acceptable
                input is one of ('desc', 'vlan', None). if search_type is set
                to None, search_word will be ignored, and all ethernet ports
                will be captured.
            :param filter_keyword: keyword to look for in switch ports property
                descriptions. defaults to "UNUSED" for
                port description, "2" for vlan
        """
        args = locals()
        # Start gathering switch-specific info
        self.swInfo = dict()
        self.swInfo['IP'] = ip_address
        switch_OIDs = [oids['sysName'], oids['sysDescr']]
        name, desc = snmpgetbulk(community_string, ip_address, switch_OIDs,
                                 port, timeout)
        self.swInfo['name'] = self._get_sw_name(name[1])
        self.swInfo['make'] = self._get_sw_make(desc[1])
        self.swInfo['model'] = self._get_sw_model(desc[1])

        self.portTable =

        raw_if_table = snmptable(community_string, ip_address,
                                 oids['ifTable'], port, timeout,
                                 sortkey='ifIndex')

        if_map = {item['ifIndex']: item for item in raw_if_table}

        raw_vlan_list = snmpwalk(community_string, ip_address,
                                 oids[self.swInfo['make']]['nativeVlan'], port,
                                 timeout)
        vlan_map = {index.split('.')[-1]: vlan for (index,vlan) in
                    raw_vlan_list}

        if_index_list = self._get_interface_list(raw_if_table)

        raw_ifx_table = snmptable(community_string, ip_address,
                                  oids['ifTable'], port, timeout,
                                  sortkey='index')

        ifx_map = {item['ifIndex']: item for item in raw_ifx_table}

        # Start gathering port-specific info for each port
        if verbosity > 0:
            print("Gathering port data...")
            progress = progressbar.ProgressBar().start(
                max_value=len(if_index_list))
        self.portTable = []

        # Run through the list of interfaces retrieved from the switch, and get
        # information on each one.
        for count, ifIndex in enumerate(if_index_list):
            if verbosity > 0: progress.update(count)
            interface = dict()
            interface['vlan'] = self.get_native_vlan(ifIndex, vlan_map)
            interface['name'] = self.get_interface_name(ifIndex, ifx_map)
            interface['desc'] = self.get_interface_description(ifIndex, ifx_map)

            # Only add an interface to the list if it's an ethernet port
            if self.get_interface_type(ifIndex, if_map) == 'ethernet':
                self.portTable.append(interface)
        if verbosity > 0: progress.finish()

        # Once the loop is done, check to see if it found anything.
        # If so, return the list of found items. if not, return none
        if len(self.portTable) == 0:
            self.portTable = None
            self.result = None
        elif filter_type:
            self.filter_table(filter_type, filter_keyword)
        else:
            self.result = self.portTable

    def filter_table(self, filter_type, filter_keyword):
        """

        :param filter_type:
        :param filter_keyword:
        :return:
        """
        if filter_keyword is None and filter_type == 'desc':
            filter_keyword = 'UNUSED'
        if filter_keyword is None and filter_type == 'vlan':
            filter_keyword = '2'

        if self.portTable:
            self.result = []
            for interface in self.portTable:
                if filter_type == 'desc' and re.search(filter_keyword,
                                                       interface['desc']):
                    self.result.append(interface)
                elif re.search('\b' + filter_keyword + '\b',
                               interface[filter_type]):
                    self.result.append(interface)
        else:
            self.result = None

    def printInfo(self):
        """

        """
        print("IP: {0} Name: {1} Make: {2} Model: {3}".format(
            self.swInfo['IP'], self.swInfo['name'], self.swInfo['make'],
            self.swInfo['model']))
        if self.result == None:
            print("No port descriptions were found matching " + "")
        else:
            for item in self.result:
                print("   Port: {0}   Vlan: {1}    Desc: {2}".format(item[
                    'name'].ljust(25), item['vlan'].ljust(14), item['desc']))
            print("Number of ports listed: " + str(len(self.result)))

    ########################
    #  Internal Functions  #
    ########################
    def _get_sw_name(self, name: str) -> str:
        if name == '':
            return "No name defined"
        else:
            return name

    def _get_sw_make(self, desc: str) -> str:
        if 'Cisco' in desc:
            return 'Cisco'
        if 'Nortel' in desc or 'Avaya' in desc:
            return 'Nortel'
        else:
            return 'Unknown: {}'.format(desc)

    def _get_sw_model(self, desc: str) -> str:
        if self.swInfo['make'] == 'Cisco':
            model_match = re.search(
                r'Cisco IOS Software, (IOS-XE Software, )'
                r'*(Catalyst )*([\S]+)\b', desc)
            if model_match:
                return model_match.group(3)
            else:
                return 'Unknown model'
        elif self.swInfo['make'] == 'Nortel':
            model_match = re.search(r'Ethernet (Routing )*Switch ([\S]+)\b',
                                    desc)
            if model_match:
                return model_match.group(2)
            else:
                return 'Unknown model'
        else:
            return 'Unknown model'

    def _get_port_table(self, args: Dict[str, Union[str, int]],) -> Dict:
        ip_address = args['ip_address']
        community_string = args['community_string']


    def _get_interface_list(self, if_table):
        index_list = [item['ifIndex'] for item in if_table]
        return index_list

    def get_native_vlan(self, index, vlan_list):
        make = self.swInfo['make']
        if make == 'Cisco' or make == 'Nortel':
            return vlan_list.get(index, None)
        else:
            #print('Native vlan detection not supported for this switch')
            return None

    def get_interface_name(self, index, interface_map):
        return interface_map[index].get('ifName', None)

    def get_interface_type(self, index, interface_map):
        iftype = interface_map[index].get('ifType', None)
        if iftype == 'ethernetCsmacd':
            # ifType is reported as a number corresponding to an IANAifType.
            # 6 = ethernetCsmacd, which is the IANAifType for a standard
            # ethernet port
            return 'ethernet'
        else:
            return 'unknown ifType: ' + iftype

    def get_interface_description(self, index, interface_table):
        return interface_table[index].get('ifAlias', None)


# Order of operations:
#     - get ip address to check

#     - get number of SNMP interfaces
#     - get interface type of all interfaces
#     - filter down to list of interfaces whose type matches "ethernetCsmacd"
#     - for each int in list, get interface name, description(ifAlias), and vlan
#     - return all interfaces whose description matches search word provided by
#       user (or "UNUSED" if no search word provided)
