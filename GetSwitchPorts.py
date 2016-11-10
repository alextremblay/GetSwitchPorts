#!/usr/bin/env python

"""
TODO: Module Docs
"""

import re  # RegEx module (internal)
from getpass import getpass  # Secure password prompt module (internal)
from sys import argv, path  # System Utilities module (internal)
from os import path as os_path  # Operating System module (internal)
path.append(os_path.join(os_path.realpath(__file__), 'modules'))  # Adds local dir 'modules' to path for module loading

from easysnmp import Session  # external package easysnmp.
import progressbar  # external package progressbar2



# specify some common OIDs 
oids = {
    'sysName': '.1.3.6.1.2.1.1.5.0',
    'sysDescr': '.1.3.6.1.2.1.1.1.0',
    'ifNumber': '.1.3.6.1.2.1.2.1.0',
    'ifTable': '.1.3.6.1.2.1.2.2.1',
    'ifIndex': '.1.3.6.1.2.1.2.2.1.1',
    'ifDescr': '.1.3.6.1.2.1.2.2.1.2',
    'ifType': '.1.3.6.1.2.1.2.2.1.3',
    'ifPhysAddress': '.1.3.6.1.2.1.2.2.1.6',
    'ifXTable': '.1.3.6.1.2.1.31.1.1.1',
    'ifName': '.1.3.6.1.2.1.31.1.1.1.1',
    'ifAlias': '.1.3.6.1.2.1.31.1.1.1.18',
    'dot1qVlanStaticName': '.1.3.6.1.2.1.17.7.1.4.3.1.1',
    'cisco': {
        'nativeVlan': '.1.3.6.1.4.1.9.9.68.1.2.2.1.2',  # VlanMembership_vmVlan from CISCO-VLAN-MEMBERSHIP-MIB
        'vlanTable': ''
    },
    'nortel': {
        'nativeVlan': '.1.3.6.1.4.1.2272.1.3.3.1.7',  # rcVlanPortDefaultVlanId from RC-VLAN-MIB
        'vlanTable': ''
    },
}


class SwitchInfo(object):
    def __new__(cls, ip_address, community_string, *args, **kwargs):
        """
        This method runs during class instantiation, before an instance of the class is created. This method will run
        and check to see if the switch you're trying to make an instance for exists. If the switch is unresponsive, then
        prints an error and returns a false value instead of creating an instance. Otherwise, proceeds with Python's
        normal instance creation process (init process)
        :param ip_address: see SwitchInfo.__init__
        :param community_string: see SwitchInfo.__init__
        :param args: pass through positional arguments
        :param kwargs: pass through keywords
        :return: an instance of this class, if the test succeeds. None otherwise
        """
        try:
            Session(hostname=ip_address, community=community_string, version=2).get(oids['sysDescr'])
        except Exception as e:
            print("Error: unable to connect to {0}, This switch appears to be unavailable. "
                  "\n the error message received is {1}".format(ip_address, e.message))
            return None
        else:
            obj = super(SwitchInfo, cls).__new__(cls, *args, **kwargs)
            return obj

    def __init__(self, ip_address, community_string, filter_type=None, filter_keyword=None):
        """
            This method will connect to a switch over SNMP and search the descriptions of all that device's ports
            for instances of a word of your choosing, or the word "UNUSED" if no search word is specified.

            :param ip_address: The IP of the device to poll
            :param community_string: the SNMPv2 read community string (read password) of the switch to poll
            :param filter_type: the port property to search by. acceptable input is one of ('desc', 'vlan', None).
                if search_type is set to None, search_word will be ignored, and all ethernet ports will be captured.
            :param filter_keyword: keyword to look for in switch ports property descriptions. defaults to "UNUSED" for
                port description, "2" for vlan
        """
        self.session = Session(hostname=ip_address, community=community_string, version=2)

        # Start gathering switch-specific info
        self.swInfo = dict()
        self.swInfo['IP'] = ip_address
        self.swInfo['name'] = self._get_sw_name()
        self.swInfo['make'] = self._get_sw_make()
        self.swInfo['model'] = self._get_sw_model()
        ifIndexList = self._get_interface_list()

        # Start gathering port-specific info for each port
        print("Gathering port data...")
        progress = progressbar.ProgressBar().start(max_value=len(ifIndexList))
        self.portTable = []

        # Run through the list of interfaces retrieved from the switch, and get information on each one.
        for count, ifIndex in enumerate(ifIndexList):
            progress.update(count)
            interface = dict()
            interface['vlan'] = self.getNativeVlan(ifIndex)
            interface['name'] = self.getIfName(ifIndex)
            interface['desc'] = self.getIfDescription(ifIndex)

            # Only add an interface to the list if it's an ethernet port
            if self.getIfType(ifIndex) == 'ethernet':
                self.portTable.append(interface)
        progress.finish()

        # Once the loop is done, check to see if it found anything.
        # If so, return the list of found items. if not, return none
        if len(self.portTable) == 0:
            self.portTable = None
            self.result = None
        elif filter_type:
            self.filterTable(filter_type, filter_keyword)
        else:
            self.result = self.portTable


    def filterTable(self, filter_type, filter_keyword):
        """

        :param filter_type:
        :param filter_keyword:
        :return:
        """
        if filter_keyword == None and filter_type == 'desc':
            filter_keyword = 'UNUSED'
        if filter_keyword == None and filter_type == 'vlan':
            filter_keyword = '2'

        if self.portTable:
            self.result = []
            for interface in self.portTable:
                if filter_type == 'desc' and re.search(filter_keyword, interface['desc']):
                    self.result.append(interface)
                elif re.search('\b' + filter_keyword + '\b', interface[filter_type]):
                    self.result.append(interface)
        else:
            self.result = None

    def printInfo(self):
        """

        """

        print("IP: {0} Name: {1} Make: {2} Model: {3}".format(
            self.swInfo['IP'],
            self.swInfo['name'],
            self.swInfo['make'].capitalize(),
            self.swInfo['model']
        ))
        if self.result == None:
            print("No port descriptions were found matching " + "")
        else:
            for item in self.result:
                print("   Port: {0}   Vlan: {1}    Desc: {2}".format(
                    item['name'].ljust(25),
                    item['vlan'].ljust(14),
                    item['desc']
                ))
            print("Number of ports listed: " + str(len(self.result)))

    ##########################
    ##  Internal Functions  ##
    ##########################
    def _get_sw_name(self):
        name = self.session.get(oids['sysName']).value
        if name == '':
            return "No name defined"
        else:
            return name

    def _get_sw_make(self):
        desc = self.session.get(oids['sysDescr']).value
        if re.search('Cisco', desc):
            return 'cisco'
        if re.search('Nortel', desc) or re.search('Avaya', desc):
            return 'nortel'
        else:
            return None

    def _get_sw_model(self):
        desc = self.session.get(oids['sysDescr'])
        if self.swInfo['make'] == 'cisco':
            modelMatch = re.search(r'Cisco IOS Software, (IOS-XE Software, )*(Catalyst )*([\S]+)\b', desc.value)
            if modelMatch:
                return modelMatch.group(3)
            else:
                return 'unknown model'
        elif self.swInfo['make'] == 'nortel':
            modelMatch = re.search(r'Ethernet (Routing )*Switch ([\S]+)\b', desc.value)
            if modelMatch:
                return modelMatch.group(2)
            else:
                return 'unknown model'
        else:
            return None

    def _get_interface_list(self):
        snmp_obj_list = self.session.walk(oids['ifIndex'])
        index_list = []
        for snmp_obj in snmp_obj_list:
            index_list.append(int(snmp_obj.value))
        return index_list

    def getNativeVlan(self, index):
        make = self.swInfo['make']
        if make == 'cisco' or make == 'nortel':
            vlan_snmp_obj = self.session.get((oids[make]['nativeVlan'], index))
            return vlan_snmp_obj.value
        else:
            print('Native vlan detection not supported for this switch')
            return None

    def getIfName(self, index):
        name_snmp_obj = self.session.get((oids['ifName'], index))
        return name_snmp_obj.value

    def getIfType(self, index):
        type_snmp_obj = self.session.get((oids['ifType'], index))
        if type_snmp_obj.value == '6':
            # ifType is reported as a number corresponding to an IANAifType.
            # 6 = ethernetCsmacd, which is the IANAifType for a standard ethernet port
            return 'ethernet'
        else:
            return 'unknown ifType: ' + type_snmp_obj.value

    def getIfDescription(self, index):
        alias_snmp_obj = self.session.get((oids['ifAlias'], index))
        return alias_snmp_obj.value

# Order of operations:
#     - get ip address to check
#     - check if ip is Nortel or Cisco device
#     - get number of SNMP interfaces
#     - get interface type of all interfaces
#     - filter down to list of interfaces whose type matches "ethernetCsmacd"
#     - for each int in list, get interface name, description(ifAlias), and vlan
#     - return all interfaces whose description matches search word provided by user
#       (or "UNUSED" if no search word provided)


# The code below will only run if this file is read as a script. (Ex. python GetSwitchPorts.py)
# If this file is instead being loaded as a module into another script, the following code will be ignored

def main(args, community_string):
    """
    GetSwitchPorts
    USAGE: python GetSwitchPorts.py [OPTIONS] IP_ADDRESS SNMP_COMMUNITY_STRING [SEARCH_TYPE] [SEARCH_WORD]

    DESCRIPTION: This script shows a list of all the ports on a switch that match certain criteria.

    ARGUMENTS:
        Required Args:
            IP_ADDRESS              The IP Address of the switch you'd like to connect to.
            COMMUNITY_STRING        The SNMP Read Community string to use to retrieve info from the switch.
        Optional Args:
            SEARCH_TYPE             What kind of thing to search for. choices are 'desc' or 'vlan'
            SEARCH_WORD             The keyword to search for. Can be a fragment of a port description in the case of a
                                    desc search, or it can be a number in the case of a vlan search
        OPTIONS:
            -h, --help              Show this help message and quit.

    SYNOPSIS:
        This script, when run, will connect to the switch specified as IP_ADDRESS through SNMP. It will retrieve and
        print a few basic pieces of information about that switch (hostname, make, model) and will then assemble a list
        of all the ports on the switch who's description contains either the SEARCH_WORD specified, or the word "UNUSED"
        if no SEARCH_WORD is provided.
        For every port found, this script will retrieve and display the port name, VLAN(s), and full description of the
        port.
    """

    switch = SwitchInfo(args.IP_ADDRESS, community_string, args.SEARCH_TYPE, args.SEARCH_WORD)
    switch.printInfo()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('IP_ADDRESS')
    parser.add_argument('SEARCH_TYPE', nargs='?', choices=['desc', 'vlan'])
    parser.add_argument('SEARCH_WORD', nargs='?')

    # Print help if no arguments given, otherwise run the script
    if len(argv) < 2 or argv[1] == '-h' or argv[1] == '--help':
        print(main.__doc__)
    else:
        args = parser.parse_args()
        community_string = getpass('SNMP Community String:')
        main(args, community_string)