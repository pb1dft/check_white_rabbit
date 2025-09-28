# check_white_rabbit

Nagios/Icinga plugin for monitoring [White Rabbit Switches](https://www.ohwr.org/projects/white-rabbit).  
It uses SNMP to query status and performance data and outputs Nagios-compatible status codes and perfdata.  

---

## Features

The plugin supports the following checks (`-m` option):

- **cpu** – CPU load (1, 5, 15 min averages)
- **os** – OS status
- **main** – Main system status
- **timing** – Timing system status
- **net** – Networking status
- **temp** – Temperature sensors (FPGA, PLL, PSL, PSR)
- **mem** – Memory usage (total, used, free)
- **disk** – Disk space (mountpoints, usage, perfdata)
- **ptp** – PTP synchronization (Grandmaster, servo state, delay coefficient)
- **pll** – PLL status (mode, alignment, sequence state)
- **slave** – Slave link status
- **ptpframes** – PTP frame flow
- **systemclock** – System clock status
- **sfp** – SFP transceivers (link, vendor, errors, temperature, TX/RX power)
- **endpoint** – Endpoint group status
- **swcore** – Soft Core status
- **rtu** – RTU status

---

## Installation

Clone the repository:

```bash
git clone https://github.com/pb1dft/check_white_rabbit.git
cd check_white_rabbit
```

Make the script executable:

```bash
chmod +x check_white_rabbit.py
```

Install dependencies:

```bash
pip install netsnmp-python
```

SNMP tools (`snmpwalk`, `snmpget`) must also be installed on the system.  
On Debian/Ubuntu:

```bash
sudo apt-get install snmp
```

---

## Usage

```bash
./check_white_rabbit.py -H <host> -C <community> -m <mode>
```

### Example

```bash
./check_white_rabbit.py -H 10.213.24.122 -C public -m ptp
```

Output:

```
OK: Port=wri2, GM=64:FB:81:FF:FE:2F:66:C9, Servo=TRACK_PHASE | delayCoefficient=+0.0002743
```

Nagios/Icinga exit codes are used:

- `0` = OK
- `1` = WARNING
- `2` = CRITICAL
- `3` = UNKNOWN

---

## Running Tests

This project includes a pytest test suite to validate the behavior of the
`check_white_rabbit` Nagios plugin without requiring a live White Rabbit switch.

The tests use `monkeypatch` to replace SNMP calls (`snmp_get` / `snmp_walk`) with
mock values, allowing simulation of different device states (OK, WARNING,
CRITICAL, UNKNOWN).

To run the tests:

```bash
pytest -v 
```

Or have more debug:

```bash
pytest -v -s
```

## Nagios Integration

### Commands

Add the following to `commands.cfg`:

```
define command {
    command_name    check_wr_cpu
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m cpu
}

define command {
    command_name    check_wr_os
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m os
}

define command {
    command_name    check_wr_main
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m main
}

define command {
    command_name    check_wr_timing
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m timing
}

define command {
    command_name    check_wr_net
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m net
}

define command {
    command_name    check_wr_temp
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m temp
}

define command {
    command_name    check_wr_mem
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m mem
}

define command {
    command_name    check_wr_disk
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m disk
}

define command {
    command_name    check_wr_ptp
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m ptp
}

define command {
    command_name    check_wr_pll
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m pll
}

define command {
    command_name    check_wr_slave
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m slave
}

define command {
    command_name    check_wr_ptpframes
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m ptpframes
}

define command {
    command_name    check_wr_systemclock
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m systemclock
}

define command {
    command_name    check_wr_sfp
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m sfp
}

define command {
    command_name    check_wr_endpoint
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m endpoint
}

define command {
    command_name    check_wr_swcore
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m swcore
}

define command {
    command_name    check_wr_rtu
    command_line    $USER1$/local/check_white_rabbit -H $HOSTADDRESS$ -C public -m rtu
}
```

### Services

Add services in `services.cfg`:

```
define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit CPU
    check_command           check_wr_cpu
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit OS
    check_command           check_wr_os
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Main
    check_command           check_wr_main
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Timing
    check_command           check_wr_timing
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Network
    check_command           check_wr_net
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Temp
    check_command           check_wr_temp
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Mem
    check_command           check_wr_mem
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Disk
    check_command           check_wr_disk
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit PTP
    check_command           check_wr_ptp
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit PLL
    check_command           check_wr_pll
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Slave
    check_command           check_wr_slave
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit PTP Frames
    check_command           check_wr_ptpframes
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit System Clock
    check_command           check_wr_systemclock
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit SFP
    check_command           check_wr_sfp
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Endpoint
    check_command           check_wr_endpoint
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit Swcore
    check_command           check_wr_swcore
    servicegroups           White Rabbit
}

define service {
    use                     generic-service
    hostgroup_name          White Rabbit
    service_description     Check White Rabbit RTU
    check_command           check_wr_rtu
    servicegroups           White Rabbit
}
```

---

## Contributing

Contributions are welcome! 🎉  

- Found a bug? Open an [issue](https://github.com/pb1dft/check_white_rabbit/issues).  
- Have an improvement? Submit a pull request.  
- Want to add new checks? Fork the repo and share your work.  

---

## License

This plugin is released under the **GNU GPL v2**, the same license as Nagios plugins.  

---

## Source

Project source code:  
👉 [https://github.com/pb1dft/check_white_rabbit](https://github.com/pb1dft/check_white_rabbit)

Author: **pb1dft**

