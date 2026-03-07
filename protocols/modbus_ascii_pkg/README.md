# Modbus ASCII Package

This package implements Modbus ASCII over the unified external protocol package API.

Supported methods:
- `send(ctx, request)`
- `recv(ctx, expect)`
- `rpc(ctx, request)`

Supported ops:
- `read_holding` (FC03)
- `read_input` (FC04)
- `write_single_coil` (FC05)
- `write_single_register` (FC06)
- `write_multiple_coils` (FC15)
- `write_multiple_registers` (FC16)

ASCII frame format:
- `':' + HEX + LRC + CRLF`

Request fields:
- `op`
- `unit_id`
- `address`
- `quantity` / `value` / `values`
