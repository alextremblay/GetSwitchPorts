"""
This internal module serves as an interface between the python application and
the net-snmp binaries on the host system. This module will provide a function
for each net-snmp binary used, run that binary with custom options, parse its
output, and deliver it back in a meaningful form. 
"""
# Standard Library imports
import csv
from ipaddress import ip_address
from socket import getaddrinfo, gaierror
from subprocess import run, PIPE

# Run a test on import to ensure the net-snmp binaries are installed.
try:
    run('snmpget')
except FileNotFoundError:
    raise ImportError(
        'Net-SNMP does not appear to be installed on this system, '
        'or the Net-SNMP commands are not on your PATH'
    )


class SNMPError(Exception):
    '''We'll use this error class anytime we receive a known, expected error 
    from an underlying net-snmp command we run'''
    pass


# Should handle the following cases: invalid community string, snmp timeout


def validate_ip_address(ipaddress):
    '''
        convert the IP Address string into an IPv4Address or IPv6Address
        then back into a string. This is a cheap and easy way to do IP
        address validation. If the string is not a valid address,
        a ValueError will be raised
    '''
    try:
        ipaddr = getaddrinfo(ipaddress, None)[0][4][0]
        ipaddr = ip_address(ipaddr)
        return ipaddr
    except (gaierror, ValueError):
        raise SNMPError("Invalid Address: {0} does not appear to be a valid "
                        "hostname / IP address".format(ipaddress))


def check_for_timeout(cmd, ipaddress, port):
    if b'No Response from' in cmd.stderr:
        raise SNMPError(
            "Timeout: no response received from {0}:{1}".format(
                ipaddress, port)
        )


def check_for_unknown_host(cmd, ipaddress):
    if b'Unknown host' in cmd.stderr:
        raise SNMPError(
            "Unknown host: the SNMP command could not identify {0} as a valid "
            "host.".format(ipaddress)
        )


def handle_unknown_error(cmdstr, cmd):
    raise ChildProcessError(
        "The SNMP command failed. \nAttempted Command: {0}\n Error received: "
        "{1}".format(cmdstr, str(cmd.stderr))
    )


def snmpget(community, ipaddress, oid, port=161, timeout=3):
    '''
    Runs Net-SNMP's 'snmpget' command on a given OID, and returns the result.
    '''
    ipaddress = validate_ip_address(ipaddress)

    cmdstr = "snmpget -Oqv -Pe -t {0} -r 0 -v 2c -c {1} {2}:{3} {4}"\
        .format(timeout, community, ipaddress, port, oid)

    cmd = run(cmdstr, shell=True, stdout=PIPE, stderr=PIPE)

    # Handle any errors that came up
    if cmd.returncode is not 0:
        check_for_timeout(cmd, ipaddress, port)

        # if previous check didn't generate an Error, this handler will be
        # called as a sort of catch-all
        handle_unknown_error(cmdstr, cmd)
    # Process results
    else:
        # subprocess returns stdout from completed command as a single bytes
        # string. We'll convert it into a regular python string for easier
        # handling
        cmdoutput = cmd.stdout.decode('utf-8')
        # Check for no such instance
        if 'No Such Instance' in cmdoutput:
            return None
        else:
            return cmdoutput


def snmpgetbulk(community, ipaddress, oids, port=161, timeout=3):
    '''
    Runs Net-SNMP's 'snmpget' command on a list of OIDs, and returns a list 
    of tuples of the form (oid, result).
    '''
    ipaddress = validate_ip_address(ipaddress)

    if type(oids) is not list:
        oids = [oids]

    cmdstr = "snmpget -OQfn -Pe -t {0} -r 0 -v 2c -c {1} {2}:{3} {4}" \
        .format(timeout, community, ipaddress, port, ' '.join(oids))

    cmd = run(cmdstr, shell=True, stdout=PIPE, stderr=PIPE)

    # Handle any errors that came up
    if cmd.returncode is not 0:
        check_for_timeout(cmd, ipaddress, port)

        # if previous check didn't generate an Error, this handler will be
        # called as a sort of catch-all
        handle_unknown_error(cmdstr, cmd)
    # Process results
    else:
        cmdoutput = cmd.stdout.splitlines()
        result = []
        for line in cmdoutput:
            # subprocess returns stdout from completed command as a bytes
            # string. We'll convert each line into a regular python string,
            # and separate the OID portion from the result portion
            item = line.decode('utf-8').split(' = ', 1)
            # Check for no such instance
            if 'No Such Instance' in item[1]:
                item[1] = None

            result.append(tuple(item))

        return result


def snmpwalk(community, ipaddress, oid, port=161, timeout=3):
    '''
    Runs Net-SNMP's 'snmpget' command on a list of OIDs, and returns a list 
    of tuples of the form (oid, result).
    '''
    ipaddress = validate_ip_address(ipaddress)

    cmdstr = "snmpwalk -OQfn -Pe -t {0} -r 0 -v 2c -c {1} {2}:{3} {4}" \
        .format(timeout, community, ipaddress, port, oid)

    cmd = run(cmdstr, shell=True, stdout=PIPE, stderr=PIPE)

    # Handle any errors that came up
    if cmd.returncode is not 0:
        check_for_timeout(cmd, ipaddress, port)

        # if previous check didn't generate an Error, this handler will be
        # called as a sort of catch-all
        handle_unknown_error(cmdstr, cmd)
    # Process results
    else:
        cmdoutput = cmd.stdout.splitlines()
        result = []
        for line in cmdoutput:
            # subprocess returns stdout from completed command as a bytes
            # string. We'll convert each line into a regular python string,
            # and separate the OID portion from the result portion
            item = line.decode('utf-8').split(' = ', 1)
            # Check for no such instance
            if 'No Such Instance' in item[1]:
                item[1] = None

            result.append(tuple(item))

        return result


def snmptable(community, ipaddress, oid, port=161, sortkey=None, timeout=3):
    '''
    Runs Net-SNMP's 'snmptable' command on a given OID, converts the results
    into a list of dictionaries, and optionally sorts the list by a given key.
    '''

    # We want our delimiter to be something that would never show up in the
    # wild, so we'll use the non-printable ascii character RS (Record Separator)
    DELIMITER = '\x1E'

    ipaddress = validate_ip_address(ipaddress)

    cmdstr = 'snmptable -m ALL -Pe -t {5} -r 0 -v 2c -Cif {0} -c {1} {2}:{3} ' \
             '{4}' \
        .format(DELIMITER, community, ipaddress, port, oid, timeout)

    cmd = run(cmdstr, shell=True, stdout=PIPE, stderr=PIPE)

    # Handle any errors that came up
    if cmd.returncode is not 0:
        check_for_timeout(cmd, ipaddress, port)

        if b'Was that a table?' in cmd.stderr:
            raise SNMPError(
                "The snmptable command could not identify {0} as a table. "
                "Please be sure the OID is correct, and that your net-snmp "
                "installation has a MIB available for that OID.".format(oid))
        else:
            handle_unknown_error(cmdstr, cmd)
    # Process results
    else:
        # subprocess returns stdout from completed command as a single bytes
        # string. we'll split it into a list of bytes strings, and convert
        # each into a standard python string which the csv reader can handle
        cmdoutput = cmd.stdout.splitlines()
        cmdoutput = [item.decode('utf-8') for item in cmdoutput]

        # Strip the table name and the blank line following it from the output,
        # so all that remains is the table itself
        cmdoutput = cmdoutput[2:]
        table_parser = csv.DictReader(cmdoutput, delimiter=DELIMITER)
        results = [element for element in table_parser]
        if sortkey:
            results.sort(key=lambda i: i[sortkey])
        return results
