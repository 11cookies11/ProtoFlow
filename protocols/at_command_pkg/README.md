# AT Command Package

This package provides a generic AT command flow over text channels.

Supported methods:
- `send(ctx, request)`
- `recv(ctx, expect)`
- `rpc(ctx, request)`

Request fields:
- `cmd` (required)
- `eol`: `crlf|cr|lf|none` (default `crlf`)

Expect fields:
- `status`: `ok|error|unknown`
- `contains`: substring check
- `regex`: regex check
- `size`: read size

Status rules:
- `OK` => `ok`
- `ERROR` / `+CME ERROR` / `+CMS ERROR` => `error`
