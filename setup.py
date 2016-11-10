from setuptools import setup

setup(
    name = 'GetSwitchPorts',
    version = '1.0',
    description='A python command line tool for retrieving switch & port info from Cisco & Nortel switches',
    long_description='''This is a command line tool written in python to retrieve switch and port information from a
    Cisco or Nortel network switch. (limited support for 3Com switches as well). This tool uses SNMP to gather
    information. The tool will grab and display a switch's IP address, make, model, and hostname, as well as name, vlan,
    and description for each port''',
    url='https://github.com/alextremblay/GetSwitchPorts',
    author='Alex Tremblay',
    license='LGPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',

        'Environment :: Console',

        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',

        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',

        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

        'Operating System :: MacOS',
        'Operating System :: Microsoft',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    packages = ['GetSwitchPorts'],
    install_requires=['easysnmp', 'prograssbar2'],
    entry_points = {
        'console_scripts': [
            'getswitchports = GetSwitchPorts.__main__:main'
        ]
})