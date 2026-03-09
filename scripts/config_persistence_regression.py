from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    # This regression exercises persistence logic in WebBridge, which depends on
    # Qt GUI modules. On Linux CI runners (headless), importing QtGui may fail.
    # Skip by default outside Windows unless explicitly overridden.
    if os.name != "nt" and os.environ.get("PROTOFLOW_FORCE_GUI_REGRESSION", "").strip().lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        print("[SKIP] config_persistence_regression: GUI bridge regression is skipped on non-Windows runners")
        return 0

    try:
        from ui.desktop.web_bridge import WebBridge
    except Exception as exc:
        print(f"[SKIP] config_persistence_regression: cannot import WebBridge ({exc})")
        return 0

    ok = True
    with tempfile.TemporaryDirectory(prefix="protoflow_cfg_") as tmp:
        os.environ["LOCALAPPDATA"] = tmp
        bridge = WebBridge(bus=None, comm=None, window=None, proxy_manager=None)

        # settings: create + backup + corrupt + fallback
        settings_a = bridge._settings_defaults()  # type: ignore[attr-defined]
        settings_b = {**settings_a, "uiTheme": "Light"}
        assert bridge._save_settings(settings_a)
        assert bridge._save_settings(settings_b)
        _write_text(bridge._settings_path, "{broken json")  # type: ignore[attr-defined]
        loaded_settings = bridge._load_settings()
        s1 = loaded_settings.get("uiTheme") == "Light"
        print(f"[{'PASS' if s1 else 'FAIL'}] settings_backup_fallback")
        ok = ok and s1

        # proxy pairs
        bridge._proxy_pairs = [  # type: ignore[attr-defined]
            {
                "id": "p1",
                "name": "pair",
                "hostPort": "COM1",
                "devicePort": "COM2",
                "baud": "115200",
                "status": "stopped",
                "desiredActive": False,
            }
        ]
        bridge._save_proxy_pairs()
        bridge._proxy_pairs[0]["name"] = "pair2"  # type: ignore[attr-defined]
        bridge._save_proxy_pairs()
        _write_text(bridge._proxy_pairs_path, "{oops")  # type: ignore[attr-defined]
        loaded_pairs = bridge._load_proxy_pairs()
        p1 = bool(loaded_pairs) and loaded_pairs[0].get("name") == "pair2"
        print(f"[{'PASS' if p1 else 'FAIL'}] proxy_backup_fallback")
        ok = ok and p1

        # ensure restored primary file is valid json after fallback
        try:
            json.loads(bridge._settings_path.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
            restored = True
        except Exception:
            restored = False
        print(f"[{'PASS' if restored else 'FAIL'}] restored_primary_json_valid")
        ok = ok and restored

    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
