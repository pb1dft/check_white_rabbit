import pytest
import sys
import check_white_rabbit as wr


# --- Helpers for mocking ---
def mock_snmp_get(mapping):
    def fake_get(host, community, oid):
        return mapping.get(oid, "0")
    return fake_get


def mock_snmp_walk(values):
    def fake_walk(host, community, oid):
        return values.get(oid, [])
    return fake_walk


def run_with_args(monkeypatch, args):
    """Run wr.main() with patched sys.argv and return exit code."""
    monkeypatch.setattr(sys, "argv", ["check_white_rabbit"] + args)
    with pytest.raises(SystemExit) as e:
        wr.main()
    return e.value.code


# --- Tests ---
def test_cpu_ok(monkeypatch, capsys):
    mapping = {
        wr.CPU_STATUS_OID: "1",  # status OK
        wr.CPU_NUMERIC_OIDS["cpu1"]: "10",
        wr.CPU_NUMERIC_OIDS["cpu5"]: "20",
        wr.CPU_NUMERIC_OIDS["cpu15"]: "30",
    }
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "cpu"])
    assert code == 0
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "CPU Load" in out


def test_mem_warning(monkeypatch, capsys):
    mapping = {
        wr.MEM_STATUS_OID: "3",  # WARNING
        wr.MEM_VALUE_OIDS["total"]: "1000",
        wr.MEM_VALUE_OIDS["used"]: "600",
        wr.MEM_VALUE_OIDS["usedPerc"]: "60",
        wr.MEM_VALUE_OIDS["free"]: "400",
    }
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "mem"])
    assert code == 1
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "Memory" in out


def test_disk_ok(monkeypatch, capsys):
    mapping = {wr.DISK_STATUS_OID: "1"}  # OK
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    walk = {
        wr.DISK_TABLE["mount"]: ["root"],
        wr.DISK_TABLE["size"]: ["100"],
        wr.DISK_TABLE["used"]: ["50"],
        wr.DISK_TABLE["free"]: ["50"],
        wr.DISK_TABLE["usePct"]: ["50"],
    }
    monkeypatch.setattr(wr, "snmp_walk", mock_snmp_walk(walk))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "disk"])
    assert code == 0
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "Disk" in out

@pytest.mark.parametrize("mode,oid,val,expected_code,expected_msg", [
    ("os", wr.OS_STATUS_OID, "1", 0, "OK"),
    ("main", wr.MAIN_STATUS_OID, "2", 2, "CRITICAL"),
    ("timing", wr.TIMING_STATUS_OID, "3", 1, "WARNING"),
    ("net", wr.NET_STATUS_OID, "99", 3, "UNKNOWN: 99"),  # unknown mapping
])
def test_generic_status(monkeypatch, capsys, mode, oid, val, expected_code, expected_msg):
    # patch snmp_get
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get({oid: val}))

    # patch sys.argv to simulate CLI arguments
    monkeypatch.setattr("sys.argv", ["check_white_rabbit", "-H", "127.0.0.1", "-m", mode])

    with pytest.raises(SystemExit) as e:
        wr.main()  # no arguments

    out = capsys.readouterr().out
    print(f"\n{out}")
    assert e.value.code == expected_code
    assert expected_msg in out
    assert mode.upper() in out

def test_temp_overheat(monkeypatch, capsys):
    mapping = {
        wr.TEMP_STATUS_OID: "1",  # ERROR
        wr.TEMP_VALUE_OIDS["fpga"]: "90",
        wr.TEMP_THRESH_OIDS["fpga"]: "80",
    }
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "temp"])
    assert code == 2
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "fpga" in out

def test_ptp_ok(monkeypatch, capsys):
    mapping = {wr.PTP_STATUS_OID: "1"}  # OK
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "ptp"])
    assert code == 0
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "Servo" in out

def test_ptpframes_ok(monkeypatch, capsys):
    mapping = {wr.PTPFRAMES_STATUS_OID: "1"}  # OK
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "ptpframes"])
    assert code == 0
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "PTP" in out


def test_sfp_with_problem(monkeypatch, capsys):
    mapping = {wr.SFP_STATUS_OID: "2"}  # ERROR
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    if not hasattr(wr, "SFP_TABLE"):
        wr.SFP_TABLE = {
            "port": "1.3.6.1.4.1.96.100.7.6.1.2",
            "vendor": "1.3.6.1.4.1.96.100.7.6.1.3",
            "sn": "1.3.6.1.4.1.96.100.7.6.1.4",
            "pn": "1.3.6.1.4.1.96.100.7.6.1.5",
        }

    walk = {
        wr.SFP_TABLE["port"]: ["wri1"],
        wr.SFP_TABLE["vendor"]: ["BlueOptics"],
        wr.SFP_TABLE["sn"]: ["12345"],
        wr.SFP_TABLE["pn"]: ["BO1234"],
    }
    monkeypatch.setattr(wr, "snmp_walk", mock_snmp_walk(walk))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "sfp"])
    assert code == 2
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "No detailed problems found" in out


@pytest.mark.parametrize("mode,oid", [
    ("endpoint", wr.ENDPOINT_STATUS_OID),
    ("swcore", wr.SWCORE_STATUS_OID),
    ("rtu", wr.RTU_STATUS_OID),
])
def test_new_checks(monkeypatch, capsys, mode, oid):
    mapping = {oid: "1"}  # OK
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", mode])
    assert code == 0
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert mode in out.lower() or "soft core" in out.lower()


def test_slave_ok(monkeypatch, capsys):
    mapping = {wr.SLAVE_STATUS_OID: "1"}  # OK
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "slave"])
    assert code == 0
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "slave" in out.lower()


def test_systemclock_warning(monkeypatch, capsys):
    mapping = {wr.SYSTEMCLOCK_STATUS_OID: "3"}  # WARNING
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "systemclock"])
    assert code == 1
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "system" in out.lower()


def test_pll_error(monkeypatch, capsys):
    mapping = {wr.PLL_STATUS_OID: "2"}  # ERROR
    monkeypatch.setattr(wr, "snmp_get", mock_snmp_get(mapping))

    code = run_with_args(monkeypatch, ["-H", "127.0.0.1", "-m", "pll"])
    assert code == 2
    out = capsys.readouterr().out
    print(f"\n{out}")
    assert "pll" in out.lower()

