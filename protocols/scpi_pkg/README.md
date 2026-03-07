# SCPI Package

This package provides generic SCPI command/query flow over text channels.

Supported methods:
- `send(ctx, request)`
- `recv(ctx, expect)`
- `rpc(ctx, request)`

Request fields:
- `cmd` / `command` (required)
- `eol`: `lf|crlf|cr|none` (default `lf`)
- `skip_recv` (optional in rpc)

Expect fields:
- `status`: `ok|error`
- `contains`
- `regex`
- `min_lines`
- `size`

Parsing:
- Multi-line response split into `lines`
- First line parsed into `csv` scalar list (`value/unit/raw`)
