"""
This internal module serves as an interface between the python application and
the net-snmp binaries on the host system. This module will provide a function
for each net-snmp binary used, run that binary with custom options, parse its
output, and deliver it back in a meaningful form. 
"""
# Internal module imports
import io
import csv

# External module exports
import shell


def snmptable(community, ipaddress, oid, sortkey=None):
    '''
    Runs Net-SNMP's 'snmptable' command on a given OID, converts the results
    into a list of dictionaries, and optionally sorts the list by a given key.
    '''

    # We want our delimiter to be something that would never show up in the
    # wild, so we'll use the non-printable ascii character RS (Record Separator)
    delimiter='\x1E'
    cmd = 'snmptable -v 2c -Cf {0} -c {1} {2} {3}'.format(
          delimiter, community, ipaddress, oid)
    cmdoutput = shell.shell(cmd).output()

    # Strip the table name from the output, so all that remains is the table
    # itself
    cmdoutput = cmdoutput[1:]
    table_parser = csv.DictReader(cmdoutput, delimiter=delimiter)
    results = [element for element in table_parser]
    if sortkey:
        results.sort(key=lambda i: i[sortkey])
    return results


