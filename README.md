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

```bash
chmod +x check_white_rabbit.py

```bash
pip install netsnmp-python

```bash
sudo apt-get install snmp

## Usage

```bash
./check_white_rabbit.py -H <host> -C <community> -m <mode>


## Example
```bash
./check_white_rabbit.py -H 192.168.1.100 -C public -m ptp

# Output
```bash
OK: Port=wri2, GM=64:FB:81:FF:FE:2F:66:C9, Servo=TRACK_PHASE | delayCoefficient=+0.0002743


