from __future__ import annotations

import json
import random
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import EmulatorConfig, ResponseSpec, Scenario, ScenarioRule
from .transport import Endpoint, SerialEndpoint, TcpServerEndpoint


_EOL_MAP = {
    "none": b"",
    "cr": b"\r",
    "lf": b"\n",
    "crlf": b"\r\n",
}


def _decode_bytes(data: bytes, encoding: str) -> str:
    if encoding.lower() == "hex":
        return data.hex().upper()
    return data.decode(encoding or "utf-8", errors="ignore")


def _encode_response(resp: ResponseSpec, encoding: str, default_eol: str) -> bytes:
    eol = _EOL_MAP.get((resp.eol or default_eol).strip().lower(), b"\r\n")
    if resp.hex is not None:
        return bytes.fromhex(resp.hex.replace(" ", "")) + eol
    text = resp.text or ""
    if encoding.lower() == "hex":
        return bytes.fromhex(text.replace(" ", "")) + eol
    return text.encode(encoding or "utf-8") + eol


def _send_with_chunk(endpoint: Endpoint, payload: bytes, chunk_bytes: int, chunk_interval_ms: int) -> None:
    if chunk_bytes <= 0:
        endpoint.write(payload)
        return
    size = max(1, chunk_bytes)
    for i in range(0, len(payload), size):
        endpoint.write(payload[i : i + size])
        if chunk_interval_ms > 0 and i + size < len(payload):
            time.sleep(chunk_interval_ms / 1000.0)


def _match_rule(rule: ScenarioRule, text: str) -> bool:
    kind = rule.when.type.strip().lower()
    pattern = rule.when.pattern
    if kind == "contains":
        return pattern in text
    if kind == "exact":
        return text == pattern
    if kind == "startswith":
        return text.startswith(pattern)
    if kind == "regex":
        return re.search(pattern, text) is not None
    raise ValueError(f"unsupported match type: {kind}")


class TargetEmulator:
    def __init__(self, scenario: Scenario, config: EmulatorConfig, endpoint: Optional[Endpoint] = None) -> None:
        self.scenario = scenario
        self.config = config
        self.endpoint = endpoint or self._create_endpoint(config)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._rules_hit: Dict[str, int] = {}
        self._rx_lines = 0
        self._tx_lines = 0

    @staticmethod
    def _create_endpoint(config: EmulatorConfig) -> Endpoint:
        mode = config.mode.strip().lower()
        if mode == "serial":
            if not config.serial_port:
                raise ValueError("serial mode requires serial_port")
            return SerialEndpoint(port=config.serial_port, baud=config.serial_baud)
        if mode == "tcp":
            return TcpServerEndpoint(host=config.tcp_host, port=config.tcp_port)
        raise ValueError(f"unsupported mode for default endpoint creation: {config.mode}")

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="target-emulator", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.endpoint.close()
        self._export_artifacts()

    def _record(self, kind: str, payload: Dict[str, Any]) -> None:
        item = {"ts": time.time(), "kind": kind, **payload}
        with self._lock:
            self._events.append(item)

    def _apply_rule(self, rule: ScenarioRule, rx_text: str) -> None:
        self._record("rule.hit", {"rule_id": rule.id, "rx": rx_text})
        self._rules_hit[rule.id] = int(self._rules_hit.get(rule.id, 0)) + 1
        delay_ms = max(0, int(rule.delay_ms))
        if rule.jitter_ms > 0:
            delay_ms += random.randint(0, int(rule.jitter_ms))
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        if rule.drop:
            self._record("tx.drop", {"rule_id": rule.id})
            return
        if rule.respond is not None:
            tx = _encode_response(rule.respond, encoding=self.scenario.encoding, default_eol=self.scenario.eol)
            _send_with_chunk(self.endpoint, tx, rule.respond.chunk_bytes, rule.respond.chunk_interval_ms)
            self._tx_lines += 1
            self._record("tx", {"rule_id": rule.id, "text": _decode_bytes(tx, self.scenario.encoding), "hex": tx.hex().upper()})
        if rule.close_after:
            self._record("session.close", {"rule_id": rule.id})
            self._running = False

    def _apply_fallback(self, rx_text: str) -> None:
        if self.scenario.fallback is None:
            self._record("rule.miss", {"rx": rx_text})
            return
        tx = _encode_response(self.scenario.fallback, encoding=self.scenario.encoding, default_eol=self.scenario.eol)
        _send_with_chunk(self.endpoint, tx, self.scenario.fallback.chunk_bytes, self.scenario.fallback.chunk_interval_ms)
        self._tx_lines += 1
        self._record("tx.fallback", {"text": _decode_bytes(tx, self.scenario.encoding), "hex": tx.hex().upper()})

    def _loop(self) -> None:
        rx_buf = bytearray()
        delim = _EOL_MAP.get(self.scenario.eol.lower(), b"\r\n")
        self._record("session.start", {"scenario": self.scenario.name, "mode": self.config.mode})
        while self._running:
            chunk = self.endpoint.read(self.config.read_chunk, self.config.read_timeout)
            if not chunk:
                continue
            rx_buf.extend(chunk)
            while True:
                if delim:
                    idx = rx_buf.find(delim)
                    if idx < 0:
                        break
                    raw = bytes(rx_buf[:idx])
                    del rx_buf[: idx + len(delim)]
                else:
                    raw = bytes(rx_buf)
                    rx_buf.clear()
                rx_text = _decode_bytes(raw, self.scenario.encoding).strip()
                if not rx_text:
                    continue
                self._rx_lines += 1
                self._record("rx", {"text": rx_text, "hex": raw.hex().upper()})
                handled = False
                for rule in self.scenario.rules:
                    if not rule.enabled:
                        continue
                    if rule.once and self._rules_hit.get(rule.id, 0) > 0:
                        continue
                    if _match_rule(rule, rx_text):
                        handled = True
                        self._apply_rule(rule, rx_text)
                        break
                if not handled:
                    self._apply_fallback(rx_text)
        self._record("session.stop", {})

    def _export_artifacts(self) -> None:
        out = Path(self.config.artifacts_dir).resolve()
        out.mkdir(parents=True, exist_ok=True)
        raw_path = out / "raw_log.jsonl"
        with raw_path.open("w", encoding="utf-8") as handle:
            for item in self._events:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        summary = {
            "scenario": self.scenario.name,
            "description": self.scenario.description,
            "mode": self.config.mode,
            "rx_lines": self._rx_lines,
            "tx_lines": self._tx_lines,
            "rules_hit": dict(self._rules_hit),
            "events": len(self._events),
            "ended_at": time.time(),
        }
        (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
