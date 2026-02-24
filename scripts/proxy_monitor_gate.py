from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import types
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Minimal yaml stub for environments without PyYAML.
if "yaml" not in sys.modules:
    yaml_stub = types.ModuleType("yaml")
    yaml_stub.safe_load = lambda *_args, **_kwargs: {}
    sys.modules["yaml"] = yaml_stub

from PySide6.QtCore import QCoreApplication

from infra.common.event_bus import EventBus
from ui.desktop.web_bridge import WebBridge


def _contains_window_options() -> bool:
    source = ROOT / "ui" / "frontend" / "src" / "components" / "ProxyMonitorView.vue"
    text = source.read_text(encoding="utf-8")
    return bool(re.search(r"bandwidthWindowOptions\s*=\s*\[\s*10\s*,\s*30\s*,\s*60\s*\]", text))


def run_gate() -> Dict[str, Any]:
    checks: Dict[str, bool] = {
        "create_ok": False,
        "update_ok": False,
        "toggle_ok": False,
        "capture_control_ok": False,
        "delete_ok": False,
        "window_options_ok": False,
        "proxy_signal_ok": False,
        "edge_no_channel_ok": False,
        "edge_illegal_id_ok": False,
        "edge_repeat_ops_ok": False,
    }
    errors: List[str] = []

    with tempfile.TemporaryDirectory(prefix="protoflow_proxy_gate_") as tmp:
        os.environ["LOCALAPPDATA"] = tmp
        app = QCoreApplication.instance() or QCoreApplication([])
        bus = EventBus()
        bridge = WebBridge(bus=bus, comm=None, window=None, plugin_manager=None)

        proxy_events: List[Any] = []
        capture_events: List[Any] = []
        control_events: List[Any] = []

        bridge.proxy_pairs.connect(lambda payload: proxy_events.append(payload))
        bridge.capture_status.connect(lambda payload: capture_events.append(payload))
        bus.subscribe("capture.control", lambda payload: control_events.append(payload))

        created = bridge.create_proxy_pair(
            {
                "name": "Gate Pair",
                "hostPort": "COM3",
                "devicePort": "COM5",
                "baud": "115200",
                "capability": "config-only",
            }
        )
        app.processEvents()
        if isinstance(created, dict) and created.get("id") and bridge.list_proxy_pairs():
            checks["create_ok"] = True
        else:
            errors.append("create_proxy_pair failed")

        updated = bridge.update_proxy_pair(
            {
                "id": created.get("id"),
                "name": "Gate Pair Updated",
                "hostPort": "COM4",
            }
        )
        app.processEvents()
        if isinstance(updated, dict) and updated.get("name") == "Gate Pair Updated" and updated.get("hostPort") == "COM4":
            checks["update_ok"] = True
        else:
            errors.append("update_proxy_pair failed")

        active_pair = bridge.set_proxy_pair_status(str(created.get("id")), True)
        inactive_pair = bridge.set_proxy_pair_status(str(created.get("id")), False)
        app.processEvents()
        if active_pair.get("status") in {"configured", "running"} and inactive_pair.get("status") == "stopped":
            checks["toggle_ok"] = True
        else:
            errors.append("set_proxy_pair_status failed")

        bridge.start_capture({"id": created.get("id"), "channel": "COM4"})
        bridge.stop_capture()
        app.processEvents()
        if (
            len(control_events) >= 2
            and isinstance(control_events[0], dict)
            and control_events[0].get("action") == "start"
            and isinstance(control_events[-1], dict)
            and control_events[-1].get("action") == "stop"
            and any(isinstance(evt, dict) and evt.get("status") == "running" for evt in capture_events)
            and any(isinstance(evt, dict) and evt.get("status") == "stopped" for evt in capture_events)
        ):
            checks["capture_control_ok"] = True
        else:
            errors.append("capture control linkage failed")

        # Edge 1: start capture without channel should fail.
        checks["edge_no_channel_ok"] = bridge.start_capture({}) is False
        if not checks["edge_no_channel_ok"]:
            errors.append("edge case no channel failed")

        # Edge 2: illegal/non-existent ids should return empty/false result.
        illegal_toggle = bridge.set_proxy_pair_status("non-existent-id", True)
        illegal_delete = bridge.delete_proxy_pair("non-existent-id")
        checks["edge_illegal_id_ok"] = (not illegal_toggle) and (illegal_delete is False)
        if not checks["edge_illegal_id_ok"]:
            errors.append("edge case illegal id failed")

        deleted = bridge.delete_proxy_pair(str(created.get("id")))
        deleted_again = bridge.delete_proxy_pair(str(created.get("id")))
        stop_again = bridge.set_proxy_pair_status(str(created.get("id")), False)
        app.processEvents()
        checks["edge_repeat_ops_ok"] = (deleted_again is False) and (not stop_again)
        if not checks["edge_repeat_ops_ok"]:
            errors.append("edge case repeat operations failed")

        if deleted and not bridge.list_proxy_pairs():
            checks["delete_ok"] = True
        else:
            errors.append("delete_proxy_pair failed")

        checks["window_options_ok"] = _contains_window_options()
        if not checks["window_options_ok"]:
            errors.append("bandwidth window options 10/30/60 not found")

        checks["proxy_signal_ok"] = len(proxy_events) >= 4
        if not checks["proxy_signal_ok"]:
            errors.append("proxy_pairs signal not emitted as expected")

    passed = all(checks.values()) and not errors
    return {"passed": passed, "checks": checks, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description="Proxy monitor gate for P2-05")
    parser.add_argument("--json-out", default="", help="Write JSON result to file")
    args = parser.parse_args()

    report = run_gate()
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
