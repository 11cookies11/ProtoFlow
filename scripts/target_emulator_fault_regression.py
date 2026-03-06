from __future__ import annotations

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


def _send(client, text: str) -> None:
    client.write(text.encode("utf-8") + b"\r\n")


def _recv(client, timeout: float = 0.5) -> str:
    data = client.read(1024, timeout=timeout)
    return data.decode("utf-8", errors="ignore")


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory(prefix="target_fault_") as tmp:
        client, server = create_mock_pair()
        scenario = load_scenario(ROOT / "tools" / "target_emulator" / "scenarios" / "fault_injection_matrix.yaml")
        emu = TargetEmulator(scenario, EmulatorConfig(mode="mock", artifacts_dir=str(Path(tmp) / "artifacts")), endpoint=server)
        emu.start()
        try:
            _send(client, "PING:DROP")
            drop_resp = _recv(client, timeout=0.15)
            ok &= _check("drop_once", drop_resp == "")

            _send(client, "PING:JITTER")
            t0 = time.time()
            jitter_resp = _recv(client, timeout=0.8)
            dt = (time.time() - t0) * 1000
            ok &= _check("jitter_resp", "PONG:JITTER" in jitter_resp and dt >= 20)

            _send(client, "PING:CHUNK")
            chunk_resp = _recv(client, timeout=0.8)
            ok &= _check("chunk_resp", "PAYLOAD:ABCDEFGHIJKLMNOPQRSTUVWXYZ" in chunk_resp)

            _send(client, "PING:CLOSE")
            close_resp = _recv(client, timeout=0.6)
            ok &= _check("close_resp", "BYE" in close_resp)
        finally:
            emu.stop()
    print(f"RESULT: {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
