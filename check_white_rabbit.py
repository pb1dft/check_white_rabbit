#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# check_white_rabbit - Nagios/Icinga plugin to monitor White Rabbit Switches
#
# Author:   pb1dft (Terence Theijn)
# Source:   https://github.com/pb1dft/check_white_rabbit
# Version:  0.2
#
# Description:
#   This script queries White Rabbit Switches via SNMP and provides
#   status and performance metrics for integration into Nagios, Icinga
#   or compatible monitoring systems.
#
#   Supported checks (-m option):
#     cpu, os, main, timing, net, temp, mem, disk,
#     ptp, pll, slave, ptpframes, systemclock, sfp,
#     endpoint, swcore, rtu
#
#   Example usage:
#     ./check_white_rabbit.py -H <host> -C <community> -m ptp
#
# License:  GNU General Public License v2 (same as Nagios plugins)
# noqa: E501

import argparse
import subprocess
import sys

import netsnmp

#
# --- SNMP HELPERS ---
#


def snmp_get(host, community, oid):
    var = netsnmp.VarList(netsnmp.Varbind(oid, ''))
    session = netsnmp.Session(DestHost=host, Version=2, Community=community)
    result = session.get(var)
    if result is None or result[0] is None:
        print(f'UNKNOWN - SNMP GET failed for {oid}')
        sys.exit(3)
    return result[0]


def snmp_walk(host, community, oid):
    try:
        out = subprocess.check_output(
            ['snmpwalk', '-v2c', '-c', community, host, oid],
            universal_newlines=True
        )
        results = []
        for line in out.strip().split('\n'):
            if '=' in line:
                val = line.split('=', 1)[1].strip()
                if ':' in val:
                    val = val.split(':', 1)[1].strip()
                results.append(val)
        return results
    except Exception as e:  # noqa: B902
        print(f'UNKNOWN - SNMP WALK failed for {oid}: {e}')
        sys.exit(3)

#
# --- FORMAT HELPERS ---
#


def format_octetstring(raw):
    """Convert raw SNMP OctetString into colon-separated hex string.
       Also strip FF:FE if it's an embedded EUI-64 from a MAC."""
    if isinstance(raw, bytes):
        hexs = [f'{b:02X}' for b in raw]
    elif isinstance(raw, str):
        hexs = [f'{ord(c):02X}' for c in raw]
    else:
        return str(raw)

    # Collapse EUI-64 with FF:FE in the middle back to 6-byte MAC
    if len(hexs) == 8 and hexs[3:5] == ['FF', 'FE']:
        hexs = hexs[0:3] + hexs[5:]

    return ':'.join(hexs)


#
# --- OID DEFINITIONS ---
#

# CPU, Memory, Disk, Temp, OS, Timing, Network
CPU_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.1.4.0'
CPU_NUMERIC_OIDS = {
    'cpu1': '1.3.6.1.4.1.96.100.7.1.5.1.0',
    'cpu5': '1.3.6.1.4.1.96.100.7.1.5.2.0',
    'cpu15': '1.3.6.1.4.1.96.100.7.1.5.3.0'
}

OS_STATUS_OID = '1.3.6.1.4.1.96.100.6.1.2.0'
MAIN_STATUS_OID = '1.3.6.1.4.1.96.100.6.1.1.0'
TIMING_STATUS_OID = '1.3.6.1.4.1.96.100.6.1.3.0'
NET_STATUS_OID = '1.3.6.1.4.1.96.100.6.1.4.0'

TEMP_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.1.2.0'
TEMP_VALUE_OIDS = {
    'fpga': '1.3.6.1.4.1.96.100.7.1.3.1.0',
    'pll': '1.3.6.1.4.1.96.100.7.1.3.2.0',
    'psl': '1.3.6.1.4.1.96.100.7.1.3.3.0',
    'psr': '1.3.6.1.4.1.96.100.7.1.3.4.0',
}
TEMP_THRESH_OIDS = {
    'fpga': '1.3.6.1.4.1.96.100.7.1.3.5.0',
    'pll': '1.3.6.1.4.1.96.100.7.1.3.6.0',
    'psl': '1.3.6.1.4.1.96.100.7.1.3.7.0',
    'psr': '1.3.6.1.4.1.96.100.7.1.3.8.0',
}

MEM_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.1.3.0'
MEM_VALUE_OIDS = {
    'total': '1.3.6.1.4.1.96.100.7.1.4.1.0',
    'used': '1.3.6.1.4.1.96.100.7.1.4.2.0',
    'usedPerc': '1.3.6.1.4.1.96.100.7.1.4.3.0',
    'free': '1.3.6.1.4.1.96.100.7.1.4.4.0'
}

DISK_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.1.5.0'
DISK_TABLE = {
    'mount': '1.3.6.1.4.1.96.100.7.1.6.1.2',
    'size': '1.3.6.1.4.1.96.100.7.1.6.1.3',
    'used': '1.3.6.1.4.1.96.100.7.1.6.1.4',
    'free': '1.3.6.1.4.1.96.100.7.1.6.1.5',
    'usePct': '1.3.6.1.4.1.96.100.7.1.6.1.6',
    'fs': '1.3.6.1.4.1.96.100.7.1.6.1.7',
}

# PTP
PTP_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.2.1.0'
PTP_IDS_OIDS = {
    'port': '1.3.6.1.4.1.96.100.7.5.1.2.1',
    'grandmaster': '1.3.6.1.4.1.96.100.7.5.1.3.1',
    'servoState': '1.3.6.1.4.1.96.100.7.5.1.6.1'
}
PTP_PERF_OIDS = {
    'delayCoefficient': '1.3.6.1.4.1.96.100.7.5.1.31.1'
}

# PLL
PLL_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.2.2.0'
PLL_INFO_OIDS = {
    'mode': '1.3.6.1.4.1.96.100.7.3.2.1.0',
    'seqState': '1.3.6.1.4.1.96.100.7.3.2.3.0',
    'alignState': '1.3.6.1.4.1.96.100.7.3.2.4.0'
}

# SLAVE
SLAVE_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.2.3.0'

# PTP FRAMES
PTPFRAMES_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.2.4.0'

# SYSTEM CLOCK
SYSTEMCLOCK_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.2.5.0'


# SFP
SFP_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.3.1.0'
PORT_TABLE_OIDS = {
    'index': '1.3.6.1.4.1.96.100.7.6.1.1',
    'name': '1.3.6.1.4.1.96.100.7.6.1.2',
    'link': '1.3.6.1.4.1.96.100.7.6.1.3',
    'vendor': '1.3.6.1.4.1.96.100.7.6.1.7',
    'sfpError': '1.3.6.1.4.1.96.100.7.6.1.12',
    'temp': '1.3.6.1.4.1.96.100.7.6.1.17',
    'txPower': '1.3.6.1.4.1.96.100.7.6.1.20',
    'rxPower': '1.3.6.1.4.1.96.100.7.6.1.21',
}

ENDPOINT_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.3.2.0'
SWCORE_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.3.3.0'
RTU_STATUS_OID = '1.3.6.1.4.1.96.100.6.2.3.4.0'

SFP_STATUS_MAP = {
    0: 'N/A',
    1: 'OK',
    2: 'Error',
    3: 'Warning',
    4: 'Warning/N.A.',
    5: 'Bug'
}

SFP_ERROR_MAP = {
    0: 'N/A',
    1: 'sfpOk',
    2: 'sfpError',
    3: 'portDown'
}

LINK_MAP = {
    0: 'N/A',
    1: 'down',
    2: 'up'
}

#
# --- STATUS MAPS ---
#
GENERIC_STATUS_MAP = {
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    3: (1, 'WARNING'),
    4: (1, 'WARNING'),
    5: (2, 'CRITICAL'),
}

TEMP_STATUS_MAP = {
    1: (3, 'UNKNOWN - threshold not set'),
    2: (0, 'OK: Temperature normal'),
    3: (2, 'CRITICAL: Temperature too high'),
}

MEM_STATUS_MAP = {
    1: (0, 'OK: Memory OK'),
    2: (2, 'CRITICAL: Memory error'),
    3: (1, 'WARNING: Memory warning'),
    4: (1, 'WARNING: Memory N/A'),
}

DISK_STATUS_MAP = {
    1: (0, 'OK: Disk space OK'),
    2: (2, 'CRITICAL: Disk space error'),
    3: (1, 'WARNING: Disk space warning'),
    4: (1, 'WARNING: Disk space N/A'),
}

PTP_STATUS_MAP = {
    0: (3, 'N/A'),
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    6: (1, 'WARNING: First read')
}

SLAVE_STATUS_MAP = {
    0: (3, 'N/A'),
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    4: (1, 'WARNING (N/A)')
}

PTPFRAMES_STATUS_MAP = {
    0: (3, 'N/A'),
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    4: (1, 'WARNING (N/A)'),
    6: (1, 'WARNING: First read')
}

SYSTEMCLOCK_STATUS_MAP = {
    0: (3, 'N/A'),
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    3: (1, 'WARNING'),
    4: (1, 'WARNING (N/A)')
}

PLL_STATUS_MAP = {
    0: (3, 'N/A'),
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    3: (1, 'WARNING'),
    4: (1, 'WARNING/N.A.'),
    5: (2, 'BUG')
}

ENDPOINT_STATUS_MAP = {
    0: (3, 'N/A'),
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    6: (1, 'WARNING: First read')
}

SWCORE_STATUS_MAP = {
    0: (3, 'N/A'),
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    6: (1, 'WARNING: First read')
}

RTU_STATUS_MAP = {
    0: (3, 'N/A'),
    1: (0, 'OK'),
    2: (2, 'CRITICAL'),
    6: (1, 'WARNING: First read')
}

#
# --- SFP CHECK ---
#


def check_sfp(host, community):
    status_val = int(snmp_get(host, community, SFP_STATUS_OID))
    status_str = SFP_STATUS_MAP.get(status_val, f'Unknown({status_val})')

    port_names = snmp_walk(host, community, PORT_TABLE_OIDS['name'])
    port_errors = snmp_walk(host, community, PORT_TABLE_OIDS['sfpError'])
    port_vendor = snmp_walk(host, community, PORT_TABLE_OIDS['vendor'])
    port_links = snmp_walk(host, community, PORT_TABLE_OIDS['link'])
    port_temps = snmp_walk(host, community, PORT_TABLE_OIDS['temp'])
    port_txpwrs = snmp_walk(host, community, PORT_TABLE_OIDS['txPower'])
    port_rxpwrs = snmp_walk(host, community, PORT_TABLE_OIDS['rxPower'])

    problems = []
    perfdata = []

    for i, pname in enumerate(port_names):
        # Skip if SFPVN (Vendor Name) is empty
        vendor_val = port_vendor[i] if i < len(port_vendor) else ''
        if not vendor_val.strip().strip('"'):
            continue

        name = pname.decode() if isinstance(pname, bytes) else pname
        err = int(port_errors[i]) if i < len(port_errors) else 0
        link = int(port_links[i]) if i < len(port_links) else 0
        temp = int(port_temps[i]) if i < len(port_temps) else 0
        txp = int(port_txpwrs[i]) if i < len(port_txpwrs) else 0
        rxp = int(port_rxpwrs[i]) if i < len(port_rxpwrs) else 0

        if err != 1 or link != 2:
            err_str = SFP_ERROR_MAP.get(err, f'Unknown({err})')
            link_str = LINK_MAP.get(link, f'Unknown({link})')
            problems.append(f'{name}: {err_str}, link={link_str}')

        perfdata.append(f'{name}_temp={temp}')
        perfdata.append(f'{name}_txPower={txp}')
        perfdata.append(f'{name}_rxPower={rxp}')

    if status_val == 1 and not problems:
        print('OK: All SFPs OK | ' + ' '.join(perfdata))
        sys.exit(0)

    if problems:
        msg = f'{status_str}: ' + '; '.join(problems)
    else:
        msg = f'{status_str}: No detailed problems found'

    exitcode = 2 if status_val == 2 else 1
    print(msg + ' | ' + ' '.join(perfdata))
    sys.exit(exitcode)

#
# --- MAIN ---
#


def main():

    parser = argparse.ArgumentParser(description='Nagios plugin for White Rabbit switch')
    parser.add_argument('-H', '--host', required=True, help='Hostname or IP')
    parser.add_argument('-C', '--community', default='public', help='SNMP community string')
    parser.add_argument('-m', '--mode', required=True, choices=[
        'cpu', 'os', 'main', 'timing', 'net', 'temp', 'mem', 'disk',
        'ptp', 'pll', 'slave', 'ptpframes', 'systemclock', 'sfp',
        'endpoint', 'swcore', 'rtu'
    ], help='Metric to monitor')
    args = parser.parse_args()

    # CPU
    if args.mode == 'cpu':
        status_val = int(snmp_get(args.host, args.community, CPU_STATUS_OID))
        exit_code = {1: 0, 2: 2, 3: 1}.get(status_val, 3)
        status_str = ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN'][exit_code]

        numeric_vals = {k: float(snmp_get(args.host, args.community, oid)) for k, oid in CPU_NUMERIC_OIDS.items()}  # noqa: E501
        perfdata = ' '.join([f'{k}={v}' for k, v in numeric_vals.items()])

        print(f"{status_str}: CPU Load {numeric_vals['cpu1']}/{numeric_vals['cpu5']}/{numeric_vals['cpu15']} | {perfdata}")  # noqa: E501
        sys.exit(exit_code)

    # OS / MAIN / TIMING / NET
    if args.mode in ['os', 'main', 'timing', 'net']:
        oid = {
            'os': OS_STATUS_OID,
            'main': MAIN_STATUS_OID,
            'timing': TIMING_STATUS_OID,
            'net': NET_STATUS_OID
        }[args.mode]
        val = int(snmp_get(args.host, args.community, oid))
        code, msg = GENERIC_STATUS_MAP.get(val, (3, f'UNKNOWN: {val}'))
        print(f'{msg}: {args.mode.upper()} status')
        sys.exit(code)

    # TEMP
    if args.mode == 'temp':
        status_val = int(snmp_get(args.host, args.community, TEMP_STATUS_OID))
        code, msg = TEMP_STATUS_MAP.get(status_val, (3, f'UNKNOWN Temp status {status_val}'))

        temps = {k: int(snmp_get(args.host, args.community, oid)) for k, oid in TEMP_VALUE_OIDS.items()}  # noqa: E501
        thresholds = {k: int(snmp_get(args.host, args.community, oid)) for k, oid in TEMP_THRESH_OIDS.items()}  # noqa: E501

        problems = [k for k in temps if temps[k] > thresholds[k]]
        if problems:
            msg = f"'CRITICAL: Overheating in {','.join(problems)}"
            code = 2

        perf = ' '.join([f'{k}={temps[k]};{thresholds[k]};{thresholds[k]};0;' for k in temps])
        print(f'{msg} | {perf}')
        sys.exit(code)

    # MEM
    if args.mode == 'mem':
        status_val = int(snmp_get(args.host, args.community, MEM_STATUS_OID))
        code, msg = MEM_STATUS_MAP.get(status_val, (3, f'UNKNOWN Memory status {status_val}'))

        memvals = {k: int(snmp_get(args.host, args.community, oid)) for k, oid in MEM_VALUE_OIDS.items()}  # noqa: E501
        perf = ' '.join([f'{k}={v}' for k, v in memvals.items()])

        print(f"{msg}: Used {memvals['used']} / {memvals['total']} ({memvals['usedPerc']}%) | {perf}")  # noqa: E501
        sys.exit(code)

    # DISK
    if args.mode == 'disk':
        status_val = int(snmp_get(args.host, args.community, DISK_STATUS_OID))
        code, msg = DISK_STATUS_MAP.get(status_val, (3, f'UNKNOWN Disk status {status_val}'))

        mounts = snmp_walk(args.host, args.community, DISK_TABLE['mount'])
        # sizes = [int(x) for x in snmp_walk(args.host, args.community, DISK_TABLE['size'])]
        used = [int(x) for x in snmp_walk(args.host, args.community, DISK_TABLE['used'])]
        # free = [int(x) for x in snmp_walk(args.host, args.community, DISK_TABLE['free'])]
        # usePct = [int(x) for x in snmp_walk(args.host, args.community, DISK_TABLE['usePct'])]
        perf = ' '.join([f'{mount}_used={u}' for mount, u in zip(mounts, used)])

        print(f"{msg}: Mounts {', '.join(mounts)} | {perf}")
        sys.exit(code)

    # PTP
    if args.mode == 'ptp':
        status_val = int(snmp_get(args.host, args.community, PTP_STATUS_OID))
        code, msg = PTP_STATUS_MAP.get(status_val, (3, f'UNKNOWN PTP status {status_val}'))

        ptp_ids = {k: snmp_get(args.host, args.community, oid) for k, oid in PTP_IDS_OIDS.items()}
        gm = format_octetstring(ptp_ids['grandmaster'])

        perfvals = {k: snmp_get(args.host, args.community, oid) for k, oid in PTP_PERF_OIDS.items()}
        perf = ' '.join([f'{k}={v}' for k, v in perfvals.items()])

        print(f"{msg}: Port={ptp_ids['port']}, GM={gm}, Servo={ptp_ids['servoState']} | {perf}")
        sys.exit(code)

    # PTP Frames
    if args.mode == 'ptpframes':
        # Simplified: Using PTP status map
        status_val = int(snmp_get(args.host, args.community, PTPFRAMES_STATUS_OID))
        code, msg = PTP_STATUS_MAP.get(status_val, (3, f'UNKNOWN PTP Frames status {status_val}'))
        print(f'{msg}: PTP Frames status')
        sys.exit(code)

    # PLL
    if args.mode == 'pll':
        status_val = int(snmp_get(args.host, args.community, PLL_STATUS_OID))
        code, msg = PLL_STATUS_MAP.get(status_val, (3, f'UNKNOWN PLL status {status_val}'))
        print(f'{msg}: PLL status')
        sys.exit(code)

    # SLAVE
    if args.mode == 'slave':
        val = int(snmp_get(args.host, args.community, SLAVE_STATUS_OID))
        code, msg = SLAVE_STATUS_MAP.get(val, (3, f'UNKNOWN slave status {val}'))
        print(f'{msg}: Slave link status')
        sys.exit(code)

    # PTP FRAMES
    if args.mode == 'ptpframes':
        val = int(snmp_get(args.host, args.community, PTPFRAMES_STATUS_OID))
        code, msg = PTPFRAMES_STATUS_MAP.get(val, (3, f'UNKNOWN PTP frames status {val}'))
        print(f'{msg}: PTP frames flowing')
        sys.exit(code)

    # SYSTEM CLOCK
    if args.mode == 'systemclock':
        val = int(snmp_get(args.host, args.community, SYSTEMCLOCK_STATUS_OID))
        code, msg = SYSTEMCLOCK_STATUS_MAP.get(val, (3, f'UNKNOWN system clock status {val}'))
        print(f'{msg}: System clock status')
        sys.exit(code)

    # --- SFP ---
    if args.mode == 'sfp':
        check_sfp(args.host, args.community)

    # ENDPOINT STATUS
    if args.mode == 'endpoint':
        val = int(snmp_get(args.host, args.community, ENDPOINT_STATUS_OID))
        code, msg = ENDPOINT_STATUS_MAP.get(val, (3, f'UNKNOWN endpoint status {val}'))
        print(f'{msg}: Endpoint status')
        sys.exit(code)

    # SWCORE STATUS
    if args.mode == 'swcore':
        val = int(snmp_get(args.host, args.community, SWCORE_STATUS_OID))
        code, msg = SWCORE_STATUS_MAP.get(val, (3, f'UNKNOWN Soft Core status {val}'))
        print(f'{msg}: Soft Core status')
        sys.exit(code)

    # RTU STATUS
    if args.mode == 'rtu':
        val = int(snmp_get(args.host, args.community, RTU_STATUS_OID))
        code, msg = RTU_STATUS_MAP.get(val, (3, f'UNKNOWN RTU status {val}'))
        print(f'{msg}: RTU status')
        sys.exit(code)


if __name__ == '__main__':
    main()
