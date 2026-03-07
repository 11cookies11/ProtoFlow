# Protocol Package Template

## Tree

```text
my_protocol_pkg/
  protocol.yaml
  impl.py
  README.md
  vectors.yaml
```

## protocol.yaml

```yaml
id: "my_protocol"
name: "My Protocol Package"
version: "1.0.0"

entry:
  module: "impl"
  class: "ProtocolPackage"

api:
  - send
  - recv
  - rpc

config_schema: {}
message_schema: {}
```

## impl.py

```python
from __future__ import annotations


class ProtocolPackage:
    def send(self, ctx, request):
        # build and send bytes
        return {"ok": True}

    def recv(self, ctx, expect):
        # read and decode bytes
        return {"ok": True}

    def rpc(self, ctx, request):
        self.send(ctx, request)
        return self.recv(ctx, request.get("expect", {}))
```

## vectors.yaml

```yaml
version: "1"
protocol_id: "my_protocol"
cases:
  - id: "send_basic"
    kind: "send"
    input:
      request: {}
    expect:
      ok: true
```
