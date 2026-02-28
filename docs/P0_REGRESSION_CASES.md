# P0 鍥炲綊鐢ㄤ緥锛堝彲澶嶇幇姝ラ + 棰勬湡锛?
## Case 1: 浠ｇ悊鍒涘缓涓庡弬鏁版牎楠?
- 鍓嶇疆锛氳繘鍏モ€滀唬鐞嗙洃鎺р€濋〉闈?- 姝ラ锛?  1. 鏂板缓浠ｇ悊锛屼富鏈虹鍙ｇ暀绌?  2. 鐐瑰嚮淇濆瓨
  3. 涓绘満绔彛涓庤澶囩鍙ｈ缃负鍚屼竴涓鍙?  4. 鐐瑰嚮淇濆瓨
- 棰勬湡锛?  - 绗?1 姝ヤ繚瀛樺け璐ュ苟鎻愮ず鈥滆閫夋嫨涓绘満绔彛鍜岃澶囩鍙ｂ€?  - 绗?3 姝ヤ繚瀛樺け璐ュ苟鎻愮ず鈥滀富鏈虹鍙ｅ拰璁惧绔彛涓嶈兘鐩稿悓鈥?
## Case 2: 浠ｇ悊鍚姩/鍋滄闂幆

- 鍓嶇疆锛氬瓨鍦ㄤ竴涓悎娉曚唬鐞嗗
- 姝ラ锛?  1. 鐐瑰嚮浠ｇ悊寮€鍏冲惎鍔?  2. 瑙傚療鍗＄墖鐘舵€?  3. 鐐瑰嚮浠ｇ悊寮€鍏冲仠姝?- 棰勬湡锛?  - 鍚姩鍚庣姸鎬佸彉涓?`running`
  - 鍋滄鍚庣姸鎬佸彉涓?`stopped`
  - 閲嶅惎搴旂敤鍚庣姸鎬佹寜 `desiredActive` 鎭㈠涓€鑷?
## Case 3: 寮傚父鍙鍖栦笌閲嶈瘯

- 鍓嶇疆锛氫汉涓哄埗閫犵鍙ｅ崰鐢ㄥ啿绐?- 姝ラ锛?  1. 鍚姩鍐茬獊浠ｇ悊
  2. 瑙傚療鍗＄墖鐘舵€佷笌閿欒鎻愮ず
  3. 閲婃斁鍐茬獊鍚庣偣鍑烩€滈噸璇曗€?- 棰勬湡锛?  - 鐘舵€佷负 `error`
  - 鍗＄墖鏄剧ず閿欒鏂囨湰
  - 閲嶈瘯鍚庡彲鎭㈠ `running`

## Case 4: 鎶撳寘鏂瑰悜涓庨€氶亾璇箟

- 鍓嶇疆锛氫唬鐞嗗浜?`running`
- 姝ラ锛?  1. 鎵撳紑鎶撳寘
  2. 浠?host 渚у彂閫佹暟鎹?  3. 浠?device 渚у彂閫佹暟鎹?- 棰勬湡锛?  - host->device 鏄犲皠涓?`TX`
  - device->host 鏄犲皠涓?`RX`
  - `channel` 璇箟绋冲畾锛屼笉闅忔潵婧愭姈鍔?
## Case 5: Mock 鍥炲綊锛堟棤椹卞姩锛?
- 鍓嶇疆锛歚.venv` 鍙敤
- 姝ラ锛?  1. 杩愯 `.\scripts\run_proxy_regression.ps1 -Mode mock`
  2. 杩愯 `.\scripts\run_proxy_regression.ps1 -Mode mock -Iterations 50 -SoakSec 60 -InjectDisconnect`
- 棰勬湡锛?  - 杈撳嚭 `RESULT: PASSED`
  - 鍖呭惈 `start_pair / host_to_device / device_to_host / proxy.data_event / status.stopped` 鍧囦负 PASS
  - 澧炲己鍥炲綊鍖呭惈 `soak.forwarding` 涓?`fault.disconnect_error_event` 涓斿潎涓?PASS

## Case 6: 铏氭嫙涓插彛/鐪熷疄璁惧鍥炲綊

- 鍓嶇疆锛氱鍙ｅ凡鍑嗗濂斤紙com0com 鎴栫湡瀹炵‖浠讹級
- 姝ラ锛?  1. 杩愯锛?     `.\scripts\run_proxy_regression.ps1 -Mode real -HostPort COM11 -DevicePort COM13 -TestHostPort COM12 -TestDevicePort COM14`
  2. 鏌ョ湅缁堢涓?JSON 鎶ュ憡
- 棰勬湡锛?  - `RESULT: PASSED`
  - 瀛愰」 `status.running / host_to_device.forward / device_to_host.forward` 鍧?PASS
  - `soak.forwarding` 鍦ㄥ惎鐢ㄦ椂 PASS

## Case 7: 閫€鍑烘竻鐞嗕竴鑷存€?
- 鍓嶇疆锛氳嚦灏戜竴涓唬鐞嗗浜?`running`
- 姝ラ锛?  1. 鍏抽棴搴旂敤
  2. 閲嶅惎搴旂敤骞惰瀵熶唬鐞嗙姸鎬?- 棰勬湡锛?  - 涓婃浼氳瘽涓嶄細娈嬬暀涓哄兊灏稿崰鐢?  - 鐘舵€佹仮澶嶉€昏緫涓€鑷达紝涓嶅嚭鐜扳€滄樉绀鸿繍琛屼絾瀹為檯涓嶅彲鐢ㄢ€?
## Case 8: comm 浜嬩欢搴忓垪涓€鑷存€э紙Mock锛?
- 鍓嶇疆锛歚.venv` 鍙敤
- 姝ラ锛?  1. 杩愯 `.\.venv\Scripts\python.exe scripts\comm_manager_regression_mock.py`
- 棰勬湡锛?  - 杈撳嚭 `RESULT: PASSED`
  - 瀛愰」 `serial_connected / serial_disconnected / tcp_connected / tcp_disconnected` 鍏ㄩ儴 PASS

## Case 9: 鍗忚瑙ｆ瀽寮傚父鎻愮ず锛圡ock锛?
- 鍓嶇疆锛歚.venv` 鍙敤
- 姝ラ锛?  1. 杩愯 `.\.venv\Scripts\python.exe scripts\packet_engine_regression.py`
- 棰勬湡锛?  - 杈撳嚭 `RESULT: PASSED`
  - 瑕嗙洊浠ヤ笅鍒ゅ畾锛?    - 姝ｅ父 Modbus 甯э細鏃犻敊璇?    - CRC 閿欒甯э細鍖呭惈 `CRC_INVALID`
    - 鐭抚锛氬寘鍚?`FRAME_TOO_SHORT`
    - 寮傚父甯ч暱搴︿笉绗︼細鍖呭惈 `LENGTH_INVALID`

## Case 10: DSL 杩愯鐢熷懡鍛ㄦ湡鍥炲綊锛圡ock锛?
- 鍓嶇疆锛歚.venv` 鍙敤
- 姝ラ锛?  1. 杩愯 `.\.venv\Scripts\python.exe scripts\script_runner_regression.py`
- 棰勬湡锛?  - 杈撳嚭 `RESULT: PASSED`
  - 姝ｅ父鎵ц璺緞鍖呭惈 `__running__` 涓?`__finished__`
  - 鍋滄璺緞鍖呭惈 `__stopped__`
  - 寮傚父璺緞鍖呭惈 `__error__`

## Case 11: 配置损坏回退回归（Mock）
- 前置：`.venv` 可用
- 姝ラ锛?  1. 杩愯 `.\.venv\Scripts\python.exe scripts\config_persistence_regression.py`
- 棰勬湡锛?  - 杈撳嚭 `RESULT: PASSED`
  - `settings_backup_fallback` 涓?PASS
  - `proxy_backup_fallback` 涓?PASS
  - `protocol_backup_fallback` 涓?PASS
  - `restored_primary_json_valid` 涓?PASS

## Case 12: 打包运行一致性回归（Mock）
- 前置：`.venv` 可用
- 步骤：
  1. 运行 `.\.venv\Scripts\python.exe scripts\package_runtime_regression.py`
- 预期：
  - 输出 `RESULT: PASSED`
  - `spec.datas_required` 为 PASS
  - `build_script.datas_required` 为 PASS
  - `installer.version_macro` 为 PASS
  - `runtime.log_path_created` 为 PASS
  - `runtime.log_contains_probe` 为 PASS
