from hub.cdp import connection_snapshot, probe_cdp


def test_probe_cdp_when_port_closed():
    result = probe_cdp(port=9, timeout=0.3)
    assert result["connected"] is False
    assert result["port"] == 9


def test_connection_snapshot_has_state():
    snap = connection_snapshot(port=9)
    assert snap["state"] in {"ready", "app_without_debug", "offline"}
    assert "summary" in snap
    assert "mcp_installed" in snap
