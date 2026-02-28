from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import serial
from serial import SerialException

from infra.common.event_bus import EventBus


_PARITY_MAP = {
    "none": serial.PARITY_NONE,
    "even": serial.PARITY_EVEN,
    "odd": serial.PARITY_ODD,
    "mark": serial.PARITY_MARK,
    "space": serial.PARITY_SPACE,
    "无": serial.PARITY_NONE,
    "偶校验": serial.PARITY_EVEN,
    "奇校验": serial.PARITY_ODD,
}

_BYTESIZE_MAP = {
    "5": serial.FIVEBITS,
    "6": serial.SIXBITS,
    "7": serial.SEVENBITS,
    "8": serial.EIGHTBITS,
}

_STOPBITS_MAP = {
    "1": serial.STOPBITS_ONE,
    "1.5": serial.STOPBITS_ONE_POINT_FIVE,
    "2": serial.STOPBITS_TWO,
}


@dataclass(frozen=True)
class StartResult:
    ok: bool
    error: str = ""


class _ProxySession:
    def __init__(self, bus: EventBus, pair_id: str, config: Dict[str, Any]) -> None:
        self._bus = bus
        self.pair_id = pair_id
        self.host_port = str(config.get("hostPort") or "").strip()
        self.device_port = str(config.get("devicePort") or "").strip()
        self._baud = int(config.get("baud") or 115200)
        self._data_bits = _BYTESIZE_MAP.get(str(config.get("dataBits") or "8"), serial.EIGHTBITS)
        parity_key = str(config.get("parity") or "none").strip().lower()
        self._parity = _PARITY_MAP.get(parity_key, serial.PARITY_NONE)
        self._stop_bits = _STOPBITS_MAP.get(str(config.get("stopBits") or "1"), serial.STOPBITS_ONE)
        self._flow = str(config.get("flowControl") or "none").strip().lower()
        self._rtscts = self._flow == "rtscts"
        self._xonxoff = self._flow == "xonxoff"
        self._host_ser: Optional[serial.Serial] = None
        self._device_ser: Optional[serial.Serial] = None
        self._threads: list[threading.Thread] = []
        self._running = threading.Event()

    def start(self) -> StartResult:
        if not self.host_port or not self.device_port:
            return StartResult(False, "host/device port is required")
        if self.host_port == self.device_port:
            return StartResult(False, "host and device port cannot be the same")
        try:
            self._host_ser = serial.Serial(
                port=self.host_port,
                baudrate=self._baud,
                bytesize=self._data_bits,
                parity=self._parity,
                stopbits=self._stop_bits,
                timeout=0.1,
                write_timeout=0.5,
                rtscts=self._rtscts,
                xonxoff=self._xonxoff,
            )
            self._device_ser = serial.Serial(
                port=self.device_port,
                baudrate=self._baud,
                bytesize=self._data_bits,
                parity=self._parity,
                stopbits=self._stop_bits,
                timeout=0.1,
                write_timeout=0.5,
                rtscts=self._rtscts,
                xonxoff=self._xonxoff,
            )
        except Exception as exc:
            self.stop()
            return StartResult(False, str(exc))

        self._running.set()
        self._threads = [
            threading.Thread(
                target=self._relay_loop,
                args=(self._host_ser, self._device_ser, self.host_port, self.device_port),
                daemon=True,
            ),
            threading.Thread(
                target=self._relay_loop,
                args=(self._device_ser, self._host_ser, self.device_port, self.host_port),
                daemon=True,
            ),
        ]
        for thread in self._threads:
            thread.start()
        return StartResult(True)

    def stop(self) -> None:
        self._running.clear()
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self._threads = []
        for ser in (self._host_ser, self._device_ser):
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass
        self._host_ser = None
        self._device_ser = None

    def _relay_loop(self, src: serial.Serial, dst: serial.Serial, src_port: str, dst_port: str) -> None:
        while self._running.is_set():
            try:
                waiting = src.in_waiting if src.is_open else 0
                if waiting <= 0:
                    time.sleep(0.01)
                    continue
                data = src.read(waiting)
                if not data:
                    continue
                dst.write(data)
                self._bus.publish(
                    "proxy.data",
                    {
                        "pair_id": self.pair_id,
                        "src": src_port,
                        "dst": dst_port,
                        "data": data,
                        "ts": time.time(),
                    },
                )
            except (SerialException, OSError) as exc:
                self._bus.publish(
                    "proxy.status",
                    {
                        "pair_id": self.pair_id,
                        "status": "error",
                        "error": str(exc),
                    },
                )
                self._running.clear()
            except Exception as exc:
                self._bus.publish(
                    "proxy.status",
                    {
                        "pair_id": self.pair_id,
                        "status": "error",
                        "error": str(exc),
                    },
                )
                self._running.clear()


class ProxyForwardManager:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._lock = threading.RLock()
        self._sessions: Dict[str, _ProxySession] = {}

    def start_pair(self, pair_id: str, config: Dict[str, Any]) -> StartResult:
        if not pair_id:
            return StartResult(False, "pair_id is required")
        with self._lock:
            old = self._sessions.pop(pair_id, None)
            if old is not None:
                old.stop()
            session = _ProxySession(self._bus, pair_id, config)
            result = session.start()
            if not result.ok:
                self._bus.publish(
                    "proxy.status",
                    {"pair_id": pair_id, "status": "error", "error": result.error},
                )
                return result
            self._sessions[pair_id] = session
            self._bus.publish("proxy.status", {"pair_id": pair_id, "status": "running", "error": None})
            return StartResult(True)

    def stop_pair(self, pair_id: str) -> None:
        if not pair_id:
            return
        with self._lock:
            session = self._sessions.pop(pair_id, None)
        if session is not None:
            session.stop()
        self._bus.publish("proxy.status", {"pair_id": pair_id, "status": "stopped", "error": None})

    def stop_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.items())
            self._sessions.clear()
        for pair_id, session in sessions:
            session.stop()
            self._bus.publish("proxy.status", {"pair_id": pair_id, "status": "stopped", "error": None})
