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

import argparse
from getpass import getpass
from sys import argv

from .GetSwitchPorts import SwitchInfo
# The code below will only run if this file is read as a script. (Ex. python GetSwitchPorts.py)
# If this file is instead being loaded as a module into another script, the following code will be ignored


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('IP_ADDRESS')
    parser.add_argument('SEARCH_TYPE', nargs='?', choices=['desc', 'vlan'])
    parser.add_argument('SEARCH_WORD', nargs='?')

    # Print help if no arguments given, otherwise run the script
    if len(argv) < 2 or argv[1] == '-h' or argv[1] == '--help':
        print(__doc__)
    else:
        args = parser.parse_args()
        community_string = getpass('SNMP Community String:')
        switch = SwitchInfo(args.IP_ADDRESS, community_string, args.SEARCH_TYPE, args.SEARCH_WORD)
        switch.printInfo()

if __name__ == '__main__':
    main()
