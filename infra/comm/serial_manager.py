"""串口管理：负责数据收发，与 EventBus 解耦，不包含协议解析。"""

from __future__ import annotations

import threading
import time
from typing import Any, List, Optional

import serial
from serial import SerialException
from serial.tools import list_ports

from infra.common.event_bus import EventBus


class SerialManager:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._ser: Optional[serial.Serial] = None
        self._rx_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._reconnecting = False
        self._port: Optional[str] = None
        self._baudrate: Optional[int] = None
        self._serial_options: dict[str, Any] = {}
        self._serial_display_options: dict[str, Any] = {}

    @property
    def port(self) -> Optional[str]:
        return self._port

    @property
    def baudrate(self) -> Optional[int]:
        return self._baudrate

    @property
    def serial_options(self) -> dict[str, Any]:
        return dict(self._serial_display_options)

    def is_open(self) -> bool:
        with self._lock:
            return bool(self._ser and self._ser.is_open)

    @staticmethod
    def list_ports() -> List[str]:
        """返回系统可用串口列表。"""
        return [port.device for port in list_ports.comports()]

    def open(
        self,
        port: str,
        baudrate: int,
        *,
        databits: int = 8,
        parity: str = "none",
        stopbits: str | float = "1",
        flow_control: str = "none",
        read_timeout_ms: int = 100,
        write_timeout_ms: int = 1000,
    ) -> bool:
        """打开串口并启动接收线程。"""
        with self._lock:
            self._stop_event.clear()
            self._reconnecting = False
            self._port, self._baudrate = port, baudrate
            self._serial_options = {
                "databits": self._normalize_databits(databits),
                "parity": self._normalize_parity(parity),
                "stopbits": self._normalize_stopbits(stopbits),
                "flow_control": self._normalize_flow_control(flow_control),
                "read_timeout_s": max(0.01, int(read_timeout_ms) / 1000.0),
                "write_timeout_s": max(0.01, int(write_timeout_ms) / 1000.0),
            }
            self._serial_display_options = {
                "dataBits": int(databits) if str(databits).isdigit() else 8,
                "parity": str(parity or "none").lower(),
                "stopBits": str(stopbits or "1"),
                "flowControl": self._serial_options["flow_control"],
                "readTimeoutMs": int(read_timeout_ms),
                "writeTimeoutMs": int(write_timeout_ms),
            }
            if self._ser and self._ser.is_open:
                self.close()
            try:
                self._ser = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    bytesize=self._serial_options["databits"],
                    parity=self._serial_options["parity"],
                    stopbits=self._serial_options["stopbits"],
                    timeout=self._serial_options["read_timeout_s"],
                    write_timeout=self._serial_options["write_timeout_s"],
                    rtscts=self._serial_options["flow_control"] == "rtscts",
                    xonxoff=self._serial_options["flow_control"] == "xonxoff",
                )
                self._running = True
                self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
                self._rx_thread.start()
                self._log(
                    f"串口打开: {port} @ {baudrate} "
                    f"(data={databits}, parity={parity}, stop={stopbits}, flow={flow_control})"
                )
                self.bus.publish("serial.opened", port)
                return True
            except SerialException as exc:
                self._log(f"[ERROR] 打开串口失败: {exc}")
                self.bus.publish("serial.error", str(exc))
                return False

    def close(self) -> None:
        """关闭串口并停止接收线程。"""
        with self._lock:
            self._running = False
            self._stop_event.set()
            self._reconnecting = False
            if self._rx_thread and self._rx_thread.is_alive():
                self._rx_thread.join(timeout=1)
            if self._ser:
                try:
                    self._ser.close()
                except Exception:
                    pass
                self._ser = None
            self._log("串口关闭")
            self.bus.publish("serial.closed")

    def send(self, data: bytes) -> None:
        """发送数据并发布发送事件。"""
        with self._lock:
            ser = self._ser
        if not ser or not ser.is_open:
            self._log("[WARN] 串口未打开，发送忽略")
            return
        try:
            ser.write(data)
            self._log(f"串口发送 {len(data)} bytes")
            self.bus.publish("serial.tx", data)
        except SerialException as exc:
            self._log(f"[ERROR] 发送失败: {exc}")
            self.bus.publish("serial.error", str(exc))

    def _rx_loop(self) -> None:
        """接收线程：非阻塞读取，异常时尝试自动重连。"""
        while self._running:
            ser = self._ser
            if not ser:
                time.sleep(0.1)
                continue

            try:
                if not ser.is_open:
                    raise SerialException("串口未打开")

                waiting = ser.in_waiting or 0
                if waiting == 0:
                    # 轻量 sleep，避免空转占用 CPU
                    time.sleep(0.02)
                    continue

                data = ser.read(waiting)
                if data:
                    self.bus.publish("serial.rx", data)
            except SerialException as exc:
                self._log(f"[ERROR] 接收异常: {exc}")
                self.bus.publish("serial.error", str(exc))
                self._attempt_reconnect()
            except Exception as exc:
                # 防止线程崩溃
                self._log(f"[ERROR] 未知接收异常: {exc}")
                self.bus.publish("serial.error", str(exc))
                time.sleep(0.1)

    def _attempt_reconnect(self) -> None:
        """自动重连，不阻塞关闭操作。"""
        with self._lock:
            if not self._running or self._stop_event.is_set():
                return
            if self._reconnecting:
                return
            self._reconnecting = True
            port, baudrate = self._port, self._baudrate
            opts = dict(self._serial_options or {})

        if not port or not baudrate:
            with self._lock:
                self._reconnecting = False
            return

        self._log(f"尝试重连串口: {port}")
        attempt = 0
        delay_s = 0.5
        max_delay_s = 5.0
        try:
            while self._running and not self._stop_event.is_set():
                attempt += 1
                try:
                    with self._lock:
                        if self._ser and self._ser.is_open:
                            return
                        if self._ser:
                            try:
                                self._ser.close()
                            except Exception:
                                pass
                            self._ser = None
                        self._ser = serial.Serial(
                            port=port,
                            baudrate=baudrate,
                            bytesize=opts.get("databits", serial.EIGHTBITS),
                            parity=opts.get("parity", serial.PARITY_NONE),
                            stopbits=opts.get("stopbits", serial.STOPBITS_ONE),
                            timeout=opts.get("read_timeout_s", 0.1),
                            write_timeout=opts.get("write_timeout_s", 1.0),
                            rtscts=opts.get("flow_control") == "rtscts",
                            xonxoff=opts.get("flow_control") == "xonxoff",
                        )
                    self._log(f"重连成功: {port} (attempt={attempt})")
                    self.bus.publish("serial.opened", port)
                    return
                except SerialException as exc:
                    self._log(f"[WARN] 重连失败 (attempt={attempt}): {exc}")
                    self.bus.publish("serial.error", f"reconnect failed (attempt={attempt}): {exc}")
                    self.bus.publish(
                        "serial.reconnecting",
                        {"port": port, "attempt": attempt, "next_delay_s": delay_s},
                    )
                    self._stop_event.wait(delay_s)
                    delay_s = min(max_delay_s, delay_s * 2.0)
        finally:
            with self._lock:
                self._reconnecting = False

    @staticmethod
    def _log(msg: str) -> None:
        # 简易日志，后续可换成 loguru/logging
        print(f"[SerialManager] {msg}")

    @staticmethod
    def _normalize_databits(value: int) -> int:
        try:
            bits = int(value)
        except (TypeError, ValueError):
            bits = 8
        mapping = {
            5: serial.FIVEBITS,
            6: serial.SIXBITS,
            7: serial.SEVENBITS,
            8: serial.EIGHTBITS,
        }
        return mapping.get(bits, serial.EIGHTBITS)

    @staticmethod
    def _normalize_parity(value: str) -> str:
        text = str(value or "none").strip().lower()
        mapping = {
            "none": serial.PARITY_NONE,
            "odd": serial.PARITY_ODD,
            "even": serial.PARITY_EVEN,
            "mark": serial.PARITY_MARK,
            "space": serial.PARITY_SPACE,
        }
        return mapping.get(text, serial.PARITY_NONE)

    @staticmethod
    def _normalize_stopbits(value: str | float) -> float:
        text = str(value or "1").strip()
        mapping = {
            "1": serial.STOPBITS_ONE,
            "1.5": serial.STOPBITS_ONE_POINT_FIVE,
            "2": serial.STOPBITS_TWO,
        }
        return mapping.get(text, serial.STOPBITS_ONE)

    @staticmethod
    def _normalize_flow_control(value: str) -> str:
        text = str(value or "none").strip().lower()
        if text in {"rtscts", "xonxoff"}:
            return text
        return "none"
