==============
GetSwitchPorts
==============

What is this?
-------------
This is a command line tool written in python to retrieve switch and port information from a Cisco or Nortel
network switch. (limited support for 3Com switches as well). This tool uses SNMP to gather information

The tool will grab and display a switch's IP address, make, model, and hostname, and will gather the following for each
port on the switch:
    * Name (how the port identify's itself, example: Gi5/47 on Cisco, ifc204 on Nortel)
    * Vlan (the native vlan / pvid on the interface. does not support trunk ports or multiple vlans)
    * Description (the port description which the switch administrator applied to the port)

Features
--------
    * Has integrated manpage-like documentation. run the cli command 'GetSwitchPorts'
    * Can retrieve info on all ports in a switch, or filter by description or by vlan
    * Automatically identifies ethernet ports and excludes all else (vlan ports, pseudo-ports, etc)
    * Shows progress while gathering port data (thanks to the excellent progressbar2 library)

Want to contribute?
-------------------
See the see the project page / wiki on github for details