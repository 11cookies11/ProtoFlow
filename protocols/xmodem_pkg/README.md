# XMODEM Package (Example)

This is an external protocol package example for ProtoFlow YAML-DSL.

Supported methods:
- `send(ctx, request)` for block or EOT frame
- `recv(ctx, expect)` for ACK/NAK or generic byte response
- `rpc(ctx, request)` send + recv

Request examples:
- block: `{"kind":"block","seq":1,"data_hex":"010203"}`
- eot: `{"kind":"eot"}`
