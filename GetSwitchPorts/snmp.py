"""
This internal module serves as an interface between the python application and
the net-snmp binaries on the host system. This module will provide a function
for each net-snmp binary used, run that binary with custom options, parse its
output, and deliver it back in a meaningful form. 
"""
# Internal module imports
import csv
from ipaddress import ip_address
from subprocess import run, PIPE

# Run a test on import to ensure the net-snmp binaries are installed.
try:
    run('snmpget', stdout=PIPE)
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
    return str(ip_address((ipaddress)))

def check_for_timeout(cmd, ipaddress, port):
    if b'No Response from' in cmd.stderr:
        raise SNMPError(
            "Timeout: no response received from {0}:{1}".format(
                ipaddress, port)
        )


def handle_unknown_error(cmdstr, cmd):
    raise ChildProcessError(
        "The SNMP command failed. \nAttempted Command: {0}\n Error received: "
        "{1}".format(cmdstr, str(cmd.stderr))
    )


def snmptable(community, ipaddress, oid, port=161, sortkey=None, timeout=3):
    '''
    Runs Net-SNMP's 'snmptable' command on a given OID, converts the results
    into a list of dictionaries, and optionally sorts the list by a given key.
    '''

    # We want our delimiter to be something that would never show up in the
    # wild, so we'll use the non-printable ascii character RS (Record Separator)
    DELIMITER = '\x1E'

    ipaddress = validate_ip_address(ipaddress)

    cmdstr = 'snmptable -m ALL -t {5} -r 0 -v 2c -Cif {0} -c {1} {2}:{3} {4}' \
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
