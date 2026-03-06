from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from dsl_runtime.protocol_package import load_protocol_packages, run_protocol_vectors
from dsl_runtime.protocol_package.gateway import ProtocolPackageGateway
from dsl_runtime.protocol_package.runtime import ProtocolCallContext


class _Channel:
    def __init__(self, rx: bytes = b"") -> None:
        self.rx = bytearray(rx)
        self.tx = bytearray()

    def write(self, data):
        if isinstance(data, str):
            self.tx.extend(data.encode("utf-8"))
        else:
            self.tx.extend(bytes(data))

    def read(self, size: int = 256, timeout: float = 0.2) -> bytes:
        if not self.rx:
            return b""
        n = min(size, len(self.rx))
        out = bytes(self.rx[:n])
        del self.rx[:n]
        return out


def _write_pkg(root: Path) -> None:
    pkg = root / "demo_pkg"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "README.md").write_text("demo", encoding="utf-8")
    (pkg / "protocol.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "demo",
                "name": "Demo Package",
                "version": "1.0.0",
                "entry": {"module": "impl", "class": "ProtocolPackage"},
                "api": ["send", "recv", "rpc"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (pkg / "impl.py").write_text(
        "\n".join(
            [
                "class ProtocolPackage:",
                "    def send(self, ctx, request):",
                "        ctx.channel.write(bytes.fromhex(request.get('hex', '')))",
                "        return {'sent': True}",
                "    def recv(self, ctx, expect):",
                "        size = int(expect.get('size', 1))",
                "        rx = ctx.channel.read(size, timeout=ctx.timeout_ms / 1000.0)",
                "        if not rx:",
                "            raise TimeoutError('timeout')",
                "        return {'rx_hex': rx.hex().upper()}",
                "    def rpc(self, ctx, request):",
                "        self.send(ctx, request)",
                "        return self.recv(ctx, request.get('expect', {}))",
            ]
        ),
        encoding="utf-8",
    )
    (pkg / "vectors.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1",
                "protocol_id": "demo",
                "cases": [
                    {"id": "send_ok", "kind": "send", "input": {"request": {"hex": "01"}}, "expect": {"ok": True}},
                    {
                        "id": "recv_ok",
                        "kind": "recv",
                        "input": {"expect": {"size": 1}, "mock_rx_hex": "06"},
                        "expect": {"ok": True},
                    },
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_pkg(root)
        load = load_protocol_packages(root)
        assert "demo" in load.packages, "package load failed"

        gateway = ProtocolPackageGateway(load.packages)
        ctx = ProtocolCallContext(channel=_Channel(rx=b"\x06"), logger=None, vars={}, timeout_ms=1000, artifacts={})
        ok = gateway.call("demo", "rpc", ctx, {"hex": "01", "expect": {"size": 1}})
        assert ok.ok, f"rpc failed: {ok.error}"
        bad = gateway.call("missing", "send", ctx, {})
        assert not bad.ok and bad.error and bad.error.get("code") == "PROTOCOL_NOT_FOUND"

        vectors = run_protocol_vectors(root, "demo")
        assert vectors.ok, "vectors run failed"
    print("protocol package regression: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
