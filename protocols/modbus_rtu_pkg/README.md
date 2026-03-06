# Modbus RTU Package (Example)

This is an external protocol package example for ProtoFlow YAML-DSL.

Supported methods:
- `send(ctx, request)`
- `recv(ctx, expect)`
- `rpc(ctx, request)`

Minimal request fields:
- `unit` (int)
- `function` (int)
- `payload_hex` (hex string without CRC)

The package appends Modbus CRC16 automatically.
