from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.target_emulator import EmulatorConfig, TargetEmulator, load_scenario
from tools.target_emulator.transport import create_mock_pair


def _check(name: str, cond: bool) -> bool:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    return cond


def _send_line(client, text: str, eol: bytes = b"\r\n") -> None:
    client.write(text.encode("utf-8") + eol)


def _read_text(client, timeout: float = 0.5) -> str:
    data = client.read(1024, timeout=timeout)
    return data.decode("utf-8", errors="ignore")


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory(prefix="target_emu_") as tmp:
        artifacts = Path(tmp) / "artifacts"
        client, server = create_mock_pair()
        scenario = load_scenario(ROOT / "tools" / "target_emulator" / "scenarios" / "at_basic.yaml")
        emu = TargetEmulator(
            scenario=scenario,
            config=EmulatorConfig(mode="mock", artifacts_dir=str(artifacts)),
            endpoint=server,
        )
        emu.start()
        try:
            _send_line(client, "AT")
            r1 = _read_text(client)
            ok &= _check("at_ok", "OK" in r1)

            _send_line(client, "ATI")
            r2 = _read_text(client)
            ok &= _check("ati_ok", "ProtoFlow-Target" in r2 and "OK" in r2)

            _send_line(client, "AT+UNKNOWN")
            r3 = _read_text(client)
            ok &= _check("fallback_error", "ERROR" in r3)
        finally:
            time.sleep(0.05)
            emu.stop()

        raw_ok = (artifacts / "raw_log.jsonl").exists()
        summary_ok = (artifacts / "summary.json").exists()
        ok &= _check("artifact_raw_log", raw_ok)
        ok &= _check("artifact_summary", summary_ok)
        if summary_ok:
            summary = json.loads((artifacts / "summary.json").read_text(encoding="utf-8"))
            ok &= _check("summary_rules_hit", int(summary.get("rules_hit", {}).get("at_ping", 0)) >= 1)

    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
