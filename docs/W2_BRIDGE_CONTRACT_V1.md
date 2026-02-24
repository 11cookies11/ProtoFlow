# WebBridge Contract v1

## 1. Scope
- Target: `ui/desktop/web_bridge.py` exposed via `QWebChannel` object `bridge`.
- Consumer: `ui/frontend/src/main.js`, `ui/frontend/src/App.vue`, `ui/frontend/src/components/ProxyMonitorView.vue`, `ui/frontend/src/stores/uiRuntime.ts`.
- Goal: freeze callable slots, emitted signals, and payload shapes for W2.

## 2. Versioning and Compatibility
- Contract version: `v1` (document-level freeze for W2).
- Compatibility rule:
  - Additive fields are allowed.
  - Removing fields, renaming fields, or changing field types is breaking.
  - Breaking changes must produce `v2` document and frontend compatibility patch in the same PR.

## 3. Transport and Encoding Rules
- QWebChannel methods may return direct values or promise-like values on frontend.
- JSON-like payloads use Qt `QVariant` (mapped to JS objects/arrays).
- Stream payload behavior:
  - `comm_rx` and `comm_tx` emit JSON strings.
  - Frontend parses with `JSON.parse` fallback to raw text.

## 4. Outbound Signals (Python -> Frontend)

### 4.1 `log: Signal(str)`
- Payload: text line.
- Purpose: runtime warnings/info.

### 4.2 `ui_ready: Signal()`
- Payload: none.
- Trigger: `notify_ready()`.

### 4.3 `comm_rx: Signal(str)` / `comm_tx: Signal(str)`
- Payload: JSON string of:
  - `text: string`
  - `hex: string` (uppercase hex without spaces)
  - `ts: number` (unix seconds, float)

### 4.4 `comm_status: Signal(object)`
- Payload shape:
  - `payload: null | string | object`
  - `ts: number`
  - `reason?: string` (only when `payload` is `null`)
- Semantic:
  - `payload == null`: disconnected
  - `payload is string`: error
  - `payload is object`: connected metadata

### 4.5 `protocol_frame: Signal(object)`
- Payload: passthrough protocol frame object from bus event `protocol.frame`.

### 4.6 `capture_frame: Signal(object)`
- Payload: capture frame object from bus event `capture.frame`.

### 4.7 `comm_batch: Signal(str)`
- Payload: JSON string array of buffered items:
  - `kind: "RX" | "TX" | "FRAME" | "CAPTURE"`
  - `payload: object`
  - optional convenience fields `text`, `hex`, `ts`

### 4.8 `script_log: Signal(str)` / `script_state: Signal(str)` / `script_progress: Signal(int)`
- Payload:
  - `script_log`: log text
  - `script_state`: state name string
  - `script_progress`: 0~100 integer

### 4.9 `channel_update: Signal(object)`
- Payload: `ChannelInfo[]` (see schema below).

### 4.10 `ui_event_log: Signal(object)`
- Payload:
  - `ts: number`
  - `emit: string`
  - `payload: any`
  - `source: any`

## 5. Inbound Slots (Frontend -> Python)

## 5.1 App/utility
- `get_app_version() -> str`
- `ping(message: str) -> str`
- `notify_ready() -> void`

## 5.2 Channel and comm
- `list_ports() -> string[]`
- `list_channels() -> ChannelInfo[]`
- `connect_serial(port: str, baud: int=115200) -> void`
- `connect_serial_advanced(payload: SerialConnectPayload) -> void`
- `connect_tcp(host: str, port: int) -> void`
- `disconnect() -> void`
- `send_text(text: str) -> void`
- `send_hex(hex_text: str) -> void` (invalid hex emits `log` warning)

## 5.3 Script/YAML
- `run_script(yaml_text: str) -> void`
- `stop_script() -> void`
- `load_yaml() -> {path,name,text} | {}`
- `save_yaml(yaml_text: str, suggested_name: str="workflow.yaml") -> {path,name} | {}`
- `parse_ui_yaml(yaml_text: str) -> {ok:true,value:any} | {ok:false,error:{message,line?,column?}}`
- `dispatch_ui_event(payload: {ts?,emit?,payload?,source?}) -> void`

## 5.4 Protocol management
- `list_protocols() -> ProtocolItem[]`
- `create_protocol(payload) -> ProtocolItem`
- `update_protocol(payload) -> ProtocolItem | {}`
- `delete_protocol(protocol_id: str) -> bool`

## 5.5 Plugin management
- `list_plugins() -> PluginItem[]`
- `refresh_plugins() -> PluginItem[]`

## 5.6 Proxy/capture
- `list_proxy_pairs() -> ProxyPair[]`
- `refresh_proxy_pairs() -> ProxyPair[]`
- `create_proxy_pair(payload) -> ProxyPair | {}`
- `update_proxy_pair(payload) -> ProxyPair | {}`
- `delete_proxy_pair(pair_id: str) -> bool`
- `set_proxy_pair_status(pair_id: str, active: bool) -> ProxyPair | {}`
- `start_capture(payload: {id?|pairId?,channel?|hostPort?}) -> bool`
- `stop_capture() -> bool`

## 5.7 Settings
- `load_settings() -> SettingsPayload`
- `save_settings(payload: SettingsPayload) -> bool`
- `select_directory(title: str, start_dir: str) -> str`

## 5.8 Window chrome (desktop host)
- `window_minimize()`
- `window_maximize()`
- `window_restore()`
- `window_toggle_maximize()`
- `window_close()`
- `window_start_move()`
- `window_start_move_at(screen_x: int, screen_y: int)`
- `window_start_resize(edge: str)`
- `window_apply_snap(screen_x: int, screen_y: int)`
- `window_show_system_menu(screen_x: int, screen_y: int)`

## 6. Core Payload Schemas

## 6.1 `ChannelInfo`
- `id: string` (format `serial:<port>` or `tcp-client:<address>`)
- `type: "serial" | "tcp-client"`
- `status: "connected" | "disconnected" | "error"`
- `port?: string`
- `baud?: number`
- `dataBits?: number`
- `parity?: string`
- `stopBits?: string`
- `flowControl?: string`
- `readTimeoutMs?: number`
- `writeTimeoutMs?: number`
- `host?: string`
- `address?: string`
- `error?: string`
- `tx_bytes: number`
- `rx_bytes: number`

## 6.2 `SerialConnectPayload`
- `port: string` (required)
- `baud?: number` default `115200`
- `dataBits?: number` default `8`
- `parity?: string` default `"none"`
- `stopBits?: string` default `"1"`
- `flowControl?: string` default `"none"`
- `readTimeoutMs?: number` default `100`
- `writeTimeoutMs?: number` default `1000`

## 6.3 `SettingsPayload`
- Top-level:
  - `uiLanguage: string`
  - `uiTheme: string`
  - `autoConnectOnStart: boolean`
  - `dslWorkspacePath: string`
- `serial`:
  - `defaultBaud: number`
  - `defaultParity: string`
  - `defaultStopBits: string`
- `network`:
  - `tcpTimeoutMs: number` (currently consumed by backend)
  - `tcpHeartbeatSec: number` (stored; not consumed by backend runtime)
  - `tcpRetryCount: number` (stored; not consumed by backend runtime)
- `runtime`:
  - `eventQueueSize: number` (stored; not consumed by backend runtime)
  - `captureBufferLimit: number` (stored; not consumed by backend runtime)
  - `uiEventRelay: boolean` (stored; not consumed by backend runtime)
- `logs`:
  - `level: string` (stored; not consumed by backend runtime logger config)
  - `retentionDays: number` (stored only)
  - `autoArchive: boolean` (stored only)
  - `includeHex: boolean` (stored only)

## 6.4 `ProtocolItem`
- Builtin fields:
  - `id`, `key`, `driver`, `desc`, `category`, `status`, `source:"builtin"`
- Custom fields:
  - `id`, `key`, `name`, `driver`, `desc`, `category`, `status`, `source:"custom"`

## 6.5 `PluginItem`
- `id: string`
- `name: string`
- `status: "enabled" | "available"`
- `enabled: boolean`
- `version: string`
- `file: string`

## 6.6 `ProxyPair`
- `id: string`
- `name: string`
- `hostPort: string`
- `devicePort: string`
- `baud: string`
- `status: "running" | "stopped"`
- `capability: string` (default `"config-only"`)
- `dataBits: string`
- `stopBits: string`
- `parity: string`
- `flowControl: string`

## 7. Error Handling Contract
- Invalid input generally returns neutral values:
  - object slots return `{}` on failure
  - boolean slots return `false`
  - list slots return `[]`
- `send_hex` on malformed hex:
  - no exception to frontend
  - emits `log` with `"invalid hex string"`
- Connection failures:
  - surfaced via `comm_status` (`payload` as string error)

## 8. Frontend Dependency Notes (Current)
- App currently prefers `comm_rx`/`comm_tx`; falls back to `comm_batch`.
- `channel_update` is consumed to refresh channel cards.
- `comm_status.payload` object fields used by UI:
  - `address`, `port`, `type`
- Settings page expects nested shape exactly as section 6.3.

## 9. W2 Freeze Checklist
- [x] Public slot list enumerated and frozen.
- [x] Public signal list enumerated and frozen.
- [x] Core payload fields documented.
- [x] Current frontend dependencies mapped.
- [x] Non-consumed stored settings explicitly marked.
