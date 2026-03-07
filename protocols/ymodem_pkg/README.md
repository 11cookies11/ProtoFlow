# YMODEM Package

This package provides YMODEM transfer flow over byte-stream channels.

Supported methods:
- `send(ctx, request)`
- `recv(ctx, expect)`
- `rpc(ctx, request)`

Primary operation:
- `op: send_data` with `data_hex`
- `op: send_file` with `file_path`

Request fields:
- `filename` (optional)
- `data_hex` or `file_path`
- `block_size`: `128|1024` (default `1024`)
- `max_retry` (default `10`)
- `timeout_ms` (optional)

Features:
- Handshake (`'C'`)
- Header packet (block 0)
- Data block transfer with retry on NAK
- EOT and end packet sequence
