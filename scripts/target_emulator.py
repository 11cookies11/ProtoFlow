from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.target_emulator import EmulatorConfig, TargetEmulator, load_scenario


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Standalone target emulator for ProtoFlow DSL regression")
    p.add_argument("--scenario", required=True, help="Scenario yaml path")
    p.add_argument("--mode", choices=["serial", "tcp"], default="serial")
    p.add_argument("--serial-port", default="")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--tcp-host", default="127.0.0.1")
    p.add_argument("--tcp-port", type=int, default=19001)
    p.add_argument("--artifacts-dir", default="./runs/target_emulator")
    p.add_argument("--max-seconds", type=int, default=0, help="Optional auto-stop timeout")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    scenario = load_scenario(args.scenario)
    cfg = EmulatorConfig(
        mode=args.mode,
        artifacts_dir=args.artifacts_dir,
        serial_port=args.serial_port or None,
        serial_baud=args.baud,
        tcp_host=args.tcp_host,
        tcp_port=args.tcp_port,
    )
    emu = TargetEmulator(scenario, cfg)
    stop_flag = {"stop": False}

    def _handle_signal(_sig, _frame):
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    emu.start()
    started = time.time()
    try:
        while not stop_flag["stop"]:
            if args.max_seconds > 0 and (time.time() - started) >= args.max_seconds:
                break
            time.sleep(0.1)
    finally:
        emu.stop()
    print(f"target emulator stopped. artifacts={Path(args.artifacts_dir).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
