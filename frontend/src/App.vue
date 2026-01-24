<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, provide, ref, watch } from 'vue'
import { basicSetup } from 'codemirror'
import { EditorState, RangeSetBuilder } from '@codemirror/state'
import { Decoration, EditorView, ViewPlugin } from '@codemirror/view'
import { HighlightStyle, syntaxHighlighting } from '@codemirror/language'
import { tags } from '@lezer/highlight'
import ManualView from './components/ManualView.vue'
import ScriptsView from './components/ScriptsView.vue'
import ProxyMonitorView from './components/ProxyMonitorView.vue'
import DropdownSelect from './components/DropdownSelect.vue'
import { yaml as yamlLanguage } from '@codemirror/lang-yaml'
import LayoutRenderer from './ui/LayoutRenderer.vue'
import { useUiRuntimeStore } from './stores/uiRuntime'

const bridge = ref(null)
const sidebarRef = ref(null)
const connectionInfo = ref({ state: 'disconnected', detail: '' })
const ports = ref([])
const selectedPort = ref('')
const baud = ref(115200)
const tcpHost = ref('127.0.0.1')
const tcpPort = ref(502)
const channelMode = ref('serial')
const sendMode = ref('text')
const displayMode = ref('ascii')
const sendText = ref('')
const sendHex = ref('')
const commLogs = ref([])
const scriptLogs = ref([])
const commPaused = ref(false)
const commLogBuffer = []
const scriptLogBuffer = []
const MAX_COMM_LOGS = 200
const MAX_SCRIPT_LOGS = 200
const MAX_RENDER_LOGS = 120
let logFlushHandle = 0
let commLogSeq = 0
let scriptLogSeq = 0
let lastStatusText = ''
let hasStatusActivity = false
const captureFrames = ref([])
const captureMeta = ref({
  channel: '',
  engine: '通用动态解析 (Agnostic Engine)',
  bufferUsed: 0,
  rangeStart: 0,
  rangeEnd: 0,
  totalFrames: 0,
  page: 1,
  pageCount: 1,
})
const captureMetrics = ref({ rtt: '--', loss: '--' })
const MAX_CAPTURE_FRAMES = 200
const scriptState = ref('idle')
const scriptProgress = ref(0)
const yamlText = ref('# paste DSL YAML here')
const scriptFileName = ref('production_test_suite_v2.yaml')
const scriptFilePath = ref('/usr/local/scripts/auto/prod/...')
const scriptRunning = ref(false)
const scriptStartMs = ref(0)
const scriptElapsedMs = ref(0)
const scriptVariablesList = ref([])
const yamlFileInputRef = ref(null)
const scriptLogRef = ref(null)
const scriptAutoScroll = ref(true)
const yamlCollapsed = ref(true)
const yamlEditorRef = ref(null)
const currentView = ref('manual')
const logKeyword = ref('')
const logTab = ref('all')
const appendCR = ref(true)
const appendLF = ref(true)
const loopSend = ref(false)
const isConnecting = ref(false)
const draggingWindow = ref(false)
const dragArmed = ref(false)
const dragStarted = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const snapPreview = ref('')
const enableSnapPreview = ref(false)
const portPlaceholder = 'COM3 - USB Serial (115200)'
const channelDialogOpen = ref(false)
const channelDialogMode = ref('create')
const channelType = ref('serial')
const channelName = ref('')
const channelPort = ref('')
const channelBaud = ref(115200)
const channelDataBits = ref('8')
const channelParity = ref('none')
const channelStopBits = ref('1')
const channelFlowControl = ref('none')
const channelReadTimeout = ref(1000)
const channelWriteTimeout = ref(1000)
const channelHost = ref('127.0.0.1')
const channelTcpPort = ref(502)
const channelAutoConnect = ref(true)
const uiLanguage = ref('zh-CN')
const uiTheme = ref('light')
const defaultBaud = ref(115200)
const defaultParity = ref('none')
const defaultStopBits = ref('1')
const tcpTimeoutMs = ref(5000)
const tcpHeartbeatSec = ref(60)
const tcpRetryCount = ref(3)
const dslWorkspacePath = ref('/usr/local/protoflow/workflows')
const autoConnectOnStart = ref(true)
const settingsSaving = ref(false)
const settingsSnapshot = ref(null)
const settingsTab = ref('general')
const zhCN = {
  'nav.manual': '串口终端',
  'nav.scripts': '自动脚本',
  'nav.proxy': '代理监控',
  'nav.protocols': '协议管理',
  'nav.settings': '设置',
  'nav.workspace': '管理员工作区',
  'header.manual.title': '串口终端',
  'header.manual.desc': '传统串口调试工具：发送命令，监听 I/O 与日志回显。',
  'header.scripts.title': '自动脚本',
  'header.scripts.desc': '用于协议解析与测试脚本自动化执行。',
  'header.proxy.title': '代理监控',
  'header.proxy.desc': '管理转发链路并实时监控数据流状态。',
  'header.protocols.title': '协议管理',
  'header.protocols.desc': '配置通信协议定义，绑定通道并设置解析规则。',
  'header.settings.title': '应用设置',
  'header.settings.desc': '管理全局偏好、协议默认值和运行时环境配置。',
  'action.refresh': '刷新',
  'action.createProtocol': '新建协议',
  'action.discardChanges': '放弃更改',
  'action.saveChanges': '保存修改',
  'action.loadScript': '加载脚本',
  'action.save': '保存',
  'badge.readOnly': '只读',
  'action.refreshStatus': '刷新状态',
  'action.newProxy': '新建转发对',
  'action.connect': '连接',
  'action.disconnect': '断开',
  'filter.all': '全部',
  'filter.running': '运行中',
  'filter.stopped': '已停止',
  'filter.error': '异常',
  'status.connected': '已连接',
  'status.disconnected': '未连接',
  'status.error': '错误',
  'status.connecting': '连接中',
  'protocol.tab.all': '全部协议',
  'protocol.tab.modbus': 'Modbus',
  'protocol.tab.tcp': 'TCP/IP',
  'protocol.tab.custom': '自定义',
  'settings.tab.general': '通用',
  'settings.tab.plugins': '插件',
  'settings.tab.runtime': '运行时',
  'settings.tab.logs': '日志',
  'settings.language': '界面语言',
  'settings.theme': '主题偏好',
  'settings.autoConnect.title': '启动时自动连接',
  'settings.autoConnect.desc': '自动尝试重连上次活动的通道。',
  'settings.workspace': '工作目录',
  'settings.chooseFolder': '选择目录',
  'settings.plugins.title': '插件管理',
  'settings.plugins.refresh': '刷新列表',
  'lang.zhCN': '简体中文',
  'lang.zhTW': '繁體中文',
  'lang.enUS': 'English (US)',
  'lang.jaJP': '日本語',
  'lang.koKR': '한국어',
  'lang.frFR': 'Français',
  'lang.deDE': 'Deutsch',
  'lang.esES': 'Español',
  'lang.ptBR': 'Português (Brasil)',
  'lang.ruRU': 'Русский',
  'lang.ar': 'العربية',
  'lang.hi': 'हिन्दी',
  'lang.itIT': 'Italiano',
  'lang.nlNL': 'Nederlands',
  'lang.thTH': 'ไทย',
  'lang.viVN': 'Tiếng Việt',
  'lang.idID': 'Bahasa Indonesia',
  'lang.trTR': 'Türkçe',
  'lang.plPL': 'Polski',
  'lang.ukUA': 'Українська',
  'theme.system': '系统默认',
  'theme.dark': '深色 (工程模式)',
  'theme.light': '浅色',
}

const enUS = {
  'nav.manual': 'Serial Terminal',
  'nav.scripts': 'Automation Scripts',
  'nav.proxy': 'Proxy Monitor',
  'nav.protocols': 'Protocol Manager',
  'nav.settings': 'Settings',
  'nav.workspace': 'Admin Workspace',
  'header.manual.title': 'Serial Terminal',
  'header.manual.desc': 'Classic serial console for sending commands, monitoring I/O and logs.',
  'header.scripts.title': 'Automation Scripts',
  'header.scripts.desc': 'Run parsing and test automation scripts.',
  'header.proxy.title': 'Proxy Monitor',
  'header.proxy.desc': 'Manage forwarding links and monitor data streams.',
  'header.protocols.title': 'Protocol Manager',
  'header.protocols.desc': 'Define protocols, bind channels, and configure parsing rules.',
  'header.settings.title': 'App Settings',
  'header.settings.desc': 'Manage global preferences, defaults, and runtime configuration.',
  'action.refresh': 'Refresh',
  'action.createProtocol': 'New Protocol',
  'action.discardChanges': 'Discard Changes',
  'action.saveChanges': 'Save Changes',
  'action.loadScript': 'Load Script',
  'action.save': 'Save',
  'badge.readOnly': 'Read-only',
  'action.refreshStatus': 'Refresh Status',
  'action.newProxy': 'New Forward Pair',
  'action.connect': 'Connect',
  'action.disconnect': 'Disconnect',
  'filter.all': 'All',
  'filter.running': 'Running',
  'filter.stopped': 'Stopped',
  'filter.error': 'Error',
  'status.connected': 'Connected',
  'status.disconnected': 'Disconnected',
  'status.error': 'Error',
  'status.connecting': 'Connecting',
  'protocol.tab.all': 'All Protocols',
  'protocol.tab.modbus': 'Modbus',
  'protocol.tab.tcp': 'TCP/IP',
  'protocol.tab.custom': 'Custom',
  'settings.tab.general': 'General',
  'settings.tab.plugins': 'Plugins',
  'settings.tab.runtime': 'Runtime',
  'settings.tab.logs': 'Logs',
  'settings.language': 'Language',
  'settings.theme': 'Theme',
  'settings.autoConnect.title': 'Auto-connect on launch',
  'settings.autoConnect.desc': 'Reconnect to the last active channel automatically.',
  'settings.workspace': 'Workspace',
  'settings.chooseFolder': 'Choose Folder',
  'settings.plugins.title': 'Plugins',
  'settings.plugins.refresh': 'Refresh List',
  'lang.zhCN': '简体中文',
  'lang.zhTW': '繁體中文',
  'lang.enUS': 'English (US)',
  'lang.jaJP': '日本語',
  'lang.koKR': '한국어',
  'lang.frFR': 'Français',
  'lang.deDE': 'Deutsch',
  'lang.esES': 'Español',
  'lang.ptBR': 'Português (Brasil)',
  'lang.ruRU': 'Русский',
  'lang.ar': 'العربية',
  'lang.hi': 'हिन्दी',
  'lang.itIT': 'Italiano',
  'lang.nlNL': 'Nederlands',
  'lang.thTH': 'ไทย',
  'lang.viVN': 'Tiếng Việt',
  'lang.idID': 'Bahasa Indonesia',
  'lang.trTR': 'Türkçe',
  'lang.plPL': 'Polski',
  'lang.ukUA': 'Українська',
  'theme.system': 'System',
  'theme.dark': 'Dark (Engineer)',
  'theme.light': 'Light',
  'Copy': 'Copy',
  'DSL 编辑器': 'DSL Editor',
  'GPS 模块数据流': 'GPS Module Data Stream',
  'IO 监控': 'I/O Monitor',
  'MQTT 适配器': 'MQTT Adapter',
  'TCP / 网络': 'TCP / Network',
  'TCP 客户端': 'TCP Client',
  'TCP 服务端': 'TCP Server',
  'TCP 端口': 'TCP Port',
  'UI YAML 预览': 'UI YAML Preview',
  'YAML UI 编辑器': 'YAML UI Editor',
  '复制': 'Copy',
  '展开': 'Expand',
  '搜索': 'Search',
  '收起': 'Collapse',
  '清空日志': 'Clear Logs',
  '滚动到底部': 'Scroll to Bottom',
  'v0.9.8 - 未安装': 'v0.9.8 - Not Installed',
  'v1.2.4 - 已启用': 'v1.2.4 - Enabled',
  '丢包率 (Packet Loss)': 'Packet Loss',
  '串口 (Serial)': 'Serial',
  '串口 (UART)': 'Serial (UART)',
  '串口参数': 'Serial Parameters',
  '串口参数配置': 'Serial Parameter Setup',
  '串口端口': 'Serial Port',
  '串口设置': 'Serial Settings',
  '串口通道': 'Serial Channel',
  '串口配置': 'Serial Configuration',
  '主控制器链路': 'Main Controller Link',
  '主机源端口': 'Host Source Port',
  '主机端口': 'Host Port',
  '代理名称': 'Proxy Name',
  '例如：192.168.1.10': 'Example: 192.168.1.10',
  '例如：CMD PING': 'Example: CMD PING',
  '例如：传感器A接口': 'Example: Sensor A Interface',
  '保存': 'Save',
  '保存修改': 'Save Changes',
  '保存后立即连接': 'Connect after saving',
  '保存配置': 'Save Configuration',
  '停止': 'Stop',
  '停止位': 'Stop Bits',
  '偶校验': 'Even Parity',
  '全部日志': 'All Logs',
  '共': 'Total',
  '写超时 (ms)': 'Write Timeout (ms)',
  '分类': 'Category',
  '列': 'Columns',
  '创建后立即启动连接': 'Start connection after creation',
  '创建指令': 'Create Command',
  '创建新的快捷调试指令': 'Create a new quick command',
  '创建通道': 'Create Channel',
  '删除': 'Delete',
  '删除前将停止转发。': 'Forwarding will stop before deletion.',
  '删除协议': 'Delete Protocol',
  '删除快捷指令': 'Delete Quick Command',
  '刷新': 'Refresh',
  '刷新串口': 'Refresh Ports',
  '动作': 'Action',
  '协议': 'Protocol',
  '协议名称': 'Protocol Name',
  '协议层级解析 (PROTOCOL TREE)': 'Protocol Tree (PROTOCOL TREE)',
  '协议桥接': 'Protocol Bridge',
  '协议详情': 'Protocol Details',
  '原始值': 'Raw Value',
  '原始十六进制 (RAW HEX)': 'Raw Hex (RAW HEX)',
  '原始数据': 'Raw Data',
  '发布规格页': 'Publish Spec Page',
  '发送数据': 'Send Data',
  '发送选项': 'Send Options',
  '取消': 'Cancel',
  '变量名': 'Variable Name',
  '变量监控': 'Variable Monitor',
  '可用': 'Available',
  '吗？': ' ?',
  '基本信息': 'Basic Info',
  '复制原始十六进制': 'Copy Raw Hex',
  '多协议通用报文分析引擎': 'Multi-Protocol Packet Analysis Engine',
  '通用动态解析 (Agnostic Engine)': 'Agnostic Parsing Engine',
  '奇校验': 'Odd Parity',
  '字段': 'Fields',
  '字节': 'Bytes',
  '实时带宽': 'Live Bandwidth',
  '实时渲染': 'Live Rendering',
  '实时网络指标': 'Live Network Metrics',
  '导出': 'Export',
  '导出分析结果': 'Export Analysis',
  '导出数据格式': 'Export Format',
  '已停止': 'Stopped',
  '已匹配协议解析插件，当前展示该报文的解析详情。': 'A protocol parser is matched. Showing parsed details for this packet.',
  '已启用': 'Enabled',
  '已用时间': 'Elapsed',
  '已禁用': 'Disabled',
  '序号': 'No.',
  '异常': 'Error',
  '引擎状态': 'Engine Status',
  '当前值': 'Current Value',
  '当前步骤:': 'Current Step:',
  '往返延时 (RTT)': 'Round-trip time (RTT)',
  '循环发送': 'Loop Send',
  '快捷指令': 'Quick Commands',
  '快捷指令编辑': 'Quick Command Editor',
  '手动解析': 'Manual Parse',
  '执行控制': 'Execution Control',
  '批量运行': 'Batch Run',
  '抓包': 'Capture',
  '报文': 'Packets',
  '报文解析详情': 'Packet Analysis Details',
  '指令内容': 'Command Content',
  '指令名称': 'Command Name',
  '接收缓冲区': 'Receive Buffer',
  '描述': 'Description',
  '搜索关键词': 'Search keywords',
  '搜索标识、十六进制、协议、原始数据...': 'Search IDs, hex, protocol, raw data...',
  '摘要 (解析结果/HEX/ASCII)': 'Summary (Parsed/HEX/ASCII)',
  '数据位': 'Data Bits',
  '文本': 'Text',
  '文档中心': 'Documentation',
  '新增快捷指令': 'Add Quick Command',
  '新建协议': 'New Protocol',
  '新建转发对': 'New Forward Pair',
  '新建通道': 'New Channel',
  '方向': 'Direction',
  '无': 'None',
  '无可用串口': 'No available serial ports',
  '无校验': 'No Parity',
  '日志采集与归档策略将在后续版本中提供。': 'Log collection and archiving policies will be available in a future release.',
  '时间戳': 'Timestamp',
  '映射模式': 'Mapping Mode',
  '显示': 'Showing',
  '暂停': 'Pause',
  '暂无十六进制数据': 'No hex data',
  '暂无协议': 'No protocols',
  '暂无协议解析数据': 'No protocol parsing data',
  '暂无可渲染的 UI 配置': 'No renderable UI configuration',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'No protocols available. Create from built-in templates or add custom.',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'No configurable items. Runtime settings will open as modules expand.',
  '暂无报文数据': 'No packet data',
  '暂无描述': 'No description',
  '未命名指令': 'Untitled Command',
  '未命名转发对': 'Unnamed Forward Pair',
  '未安装': 'Not Installed',
  '未知': 'Unknown',
  '未知协议报文 (Unknown Protocol)': 'Unknown Protocol Packet (Unknown Protocol)',
  '未选择任何组件': 'No component selected',
  '条日志记录': 'log entries',
  '查看': 'View',
  '查看或更新协议描述与分类。': 'View or update protocol description and category.',
  '查看详情': 'View Details',
  '校验位': 'Parity',
  '格式:': 'Format:',
  '波特率': 'Baud Rate',
  '活动通道': 'Active Channel',
  '流控': 'Flow Control',
  '浏览...': 'Browse...',
  '添加 CR (\r)': 'Add CR (\r)',
  '添加 LF (\n)': 'Add LF (\n)',
  '添加自定义协议元数据，供解析引擎识别。': 'Add custom protocol metadata for the parser engine.',
  '清除': 'Clear',
  '清除日志': 'Clear Logs',
  '版本': 'Version',
  '状态': 'Status',
  '电机反馈继电器': 'Motor Feedback Relay',
  '目标地址': 'Target Address',
  '确认删除': 'Confirm Delete',
  '确认删除自定义协议': 'Confirm delete custom protocol',
  '确认删除该快捷指令，删除后无法恢复。': 'Confirm delete this quick command? This action cannot be undone.',
  '确认删除转发对': 'Confirm delete forward pair',
  '离线': 'Offline',
  '空闲': 'Idle',
  '端口': 'Port',
  '第': 'Page',
  '等待 YAML 配置...': 'Waiting for YAML configuration...',
  '系统未能自动匹配已知的解析插件。您可以尝试手动配置解析规则，或使用万能解析脚本。': 'The system could not match a known parser. Try manual rules or use the universal parsing script.',
  '继续捕获': 'Resume Capture',
  '编译日期': 'Build Date',
  '编辑': 'Edit',
  '编辑或更新现有的快捷调试指令': 'Edit or update an existing quick command',
  '编辑转发代理': 'Edit Forward Proxy',
  '网络 (TCP)': 'Network (TCP)',
  '脚本运行中展示 UI 渲染结果': 'Show UI rendering while script runs',
  '自动重连': 'Auto Reconnect',
  '自定义': 'Custom',
  '行': 'Rows',
  '解析值': 'Parsed Value',
  '解析失败': 'Parse Failed',
  '解析错误': 'Parse Error',
  '设备代理端口': 'Device Proxy Port',
  '设备端口': 'Device Port',
  '详细日志': 'Verbose Logs',
  '请输入指令名称和内容': 'Enter command name and content',
  '读超时 (ms)': 'Read Timeout (ms)',
  '调整解析规则': 'Adjust parsing rules',
  '路径': 'Path',
  '转发中': 'Forwarding',
  '输入搜索...': 'Enter search...',
  '输入要发送的指令内容': 'Enter command content to send',
  '输入要发送的数据...': 'Enter data to send...',
  '过滤日志...': 'Filter logs...',
  '运行': 'Run',
  '运行中': 'Running',
  '运行日志': 'Run Logs',
  '连接失败': 'Connection Failed',
  '连接模式': 'Connection Mode',
  '选择串口': 'Select Serial Port',
  '选择工作区': 'Select Workspace',
  '选择路径': 'Select Path',
  '透传模式': 'Transparent Mode',
  '通道名称': 'Channel Name',
  '配置': 'Configure',
  '配置串口连接参数': 'Configure serial connection parameters',
  '配置协议': 'Configure Protocol',
  '配置新的通信连接参数': 'Configure new connection parameters',
  '配置解析规则': 'Configure parsing rules',
  '重置': 'Reset',
  '链路层 (Data Link Layer)': 'Data Link Layer',
  '错误数': 'Error Count',
  '键名': 'Key',
  '长度': 'Length',
  '问题反馈': 'Feedback',
  '页': '',
  '驱动': 'Driver',
  '驱动类': 'Driver Class',
  '高级选项': 'Advanced Options',
  '（两端需一致）': '(Both ends must match)',
}

const zhTW = {
  ...enUS,
  'nav.manual': '串口終端',
  'nav.scripts': '自動腳本',
  'nav.proxy': '代理監控',
  'nav.protocols': '協議管理',
  'nav.settings': '設定',
  'nav.workspace': '管理員工作區',
  'header.manual.title': '串口終端',
  'header.manual.desc': '傳統串口調試工具：發送命令，監聽 I/O 與日誌回顯。',
  'header.scripts.title': '自動腳本',
  'header.scripts.desc': '用於協議解析與測試腳本自動化執行。',
  'header.proxy.title': '代理監控',
  'header.proxy.desc': '管理轉發鏈路並即時監控資料流狀態。',
  'header.protocols.title': '協議管理',
  'header.protocols.desc': '配置通訊協議定義，綁定通道並設定解析規則。',
  'header.settings.title': '應用設定',
  'header.settings.desc': '管理全域偏好、協議預設值與執行時環境配置。',
  'action.refresh': '重新整理',
  'action.createProtocol': '新增協議',
  'action.discardChanges': '放棄變更',
  'action.saveChanges': '儲存變更',
  'action.loadScript': '載入腳本',
  'action.save': '儲存',
  'badge.readOnly': '唯讀',
  'action.refreshStatus': '重新整理狀態',
  'action.newProxy': '新增轉發對',
  'action.connect': '連線',
  'action.disconnect': '中斷連線',
  'filter.all': '全部',
  'filter.running': '執行中',
  'filter.stopped': '已停止',
  'filter.error': '異常',
  'status.connected': '已連線',
  'status.disconnected': '未連線',
  'status.error': '錯誤',
  'status.connecting': '連線中',
  'protocol.tab.all': '全部協議',
  'protocol.tab.modbus': 'Modbus',
  'protocol.tab.tcp': 'TCP/IP',
  'protocol.tab.custom': '自訂',
  'settings.tab.general': '通用',
  'settings.tab.plugins': '外掛',
  'settings.tab.runtime': '執行時',
  'settings.tab.logs': '日誌',
  'settings.language': '介面語言',
  'settings.theme': '主題偏好',
  'settings.autoConnect.title': '啟動時自動連線',
  'settings.autoConnect.desc': '自動嘗試重新連線上次活動的通道。',
  'settings.workspace': '工作目錄',
  'settings.chooseFolder': '選擇目錄',
  'settings.plugins.title': '外掛管理',
  'settings.plugins.refresh': '重新整理清單',
  'lang.zhCN': '簡體中文',
  'lang.zhTW': '繁體中文',
  'lang.enUS': 'English (US)',
  'lang.jaJP': '日本語',
  'lang.koKR': '한국어',
  'lang.frFR': 'Français',
  'lang.deDE': 'Deutsch',
  'lang.esES': 'Español',
  'lang.ptBR': 'Português (Brasil)',
  'lang.ruRU': 'Русский',
  'lang.ar': 'العربية',
  'lang.hi': 'हिन्दी',
  'lang.itIT': 'Italiano',
  'lang.nlNL': 'Nederlands',
  'lang.thTH': 'ไทย',
  'lang.viVN': 'Tiếng Việt',
  'lang.idID': 'Bahasa Indonesia',
  'lang.trTR': 'Türkçe',
  'lang.plPL': 'Polski',
  'lang.ukUA': 'Українська',
  'theme.system': '系統預設',
  'theme.dark': '深色 (工程模式)',
  'theme.light': '淺色',
}
const jaJP = {
  ...enUS,
  'nav.manual': 'シリアルターミナル',
  'nav.scripts': '自動スクリプト',
  'nav.proxy': 'プロキシ監視',
  'nav.protocols': 'プロトコル管理',
  'nav.settings': '設定',
  'nav.workspace': '管理ワークスペース',
  'header.manual.title': 'シリアルターミナル',
  'header.manual.desc': 'コマンド送信と I/O・ログを監視する従来型シリアルツール。',
  'header.scripts.title': '自動スクリプト',
  'header.scripts.desc': 'プロトコル解析とテストスクリプトの自動実行。',
  'header.proxy.title': 'プロキシ監視',
  'header.proxy.desc': '転送リンクを管理し、データストリームをリアルタイム監視します。',
  'header.protocols.title': 'プロトコル管理',
  'header.protocols.desc': '通信プロトコルを定義し、チャネルを割り当て、解析ルールを設定します。',
  'header.settings.title': 'アプリ設定',
  'header.settings.desc': '全体の設定、プロトコル既定値、実行時環境を管理します。',
  'action.refresh': '更新',
  'action.createProtocol': '新規プロトコル',
  'action.discardChanges': '変更を破棄',
  'action.saveChanges': '変更を保存',
  'action.loadScript': 'スクリプト読込',
  'action.save': '保存',
  'badge.readOnly': '読み取り専用',
  'action.refreshStatus': '状態を更新',
  'action.newProxy': '新規転送ペア',
  'action.connect': '接続',
  'action.disconnect': '切断',
  'filter.all': 'すべて',
  'filter.running': '稼働中',
  'filter.stopped': '停止',
  'filter.error': '異常',
  'status.connected': '接続済み',
  'status.disconnected': '未接続',
  'status.error': 'エラー',
  'status.connecting': '接続中',
  'protocol.tab.all': 'すべてのプロトコル',
  'protocol.tab.modbus': 'Modbus',
  'protocol.tab.tcp': 'TCP/IP',
  'protocol.tab.custom': 'カスタム',
  'settings.tab.general': '一般',
  'settings.tab.plugins': 'プラグイン',
  'settings.tab.runtime': 'ランタイム',
  'settings.tab.logs': 'ログ',
  'settings.language': '表示言語',
  'settings.theme': 'テーマ',
  'settings.autoConnect.title': '起動時に自動接続',
  'settings.autoConnect.desc': '前回のアクティブチャネルに自動再接続します。',
  'settings.workspace': 'ワークスペース',
  'settings.chooseFolder': 'フォルダを選択',
  'settings.plugins.title': 'プラグイン管理',
  'settings.plugins.refresh': '一覧を更新',
  'lang.zhCN': '簡体中文',
  'lang.zhTW': '繁體中文',
  'lang.enUS': 'English (US)',
  'lang.jaJP': '日本語',
  'lang.koKR': '한국어',
  'lang.frFR': 'Français',
  'lang.deDE': 'Deutsch',
  'lang.esES': 'Español',
  'lang.ptBR': 'Português (Brasil)',
  'lang.ruRU': 'Русский',
  'lang.ar': 'العربية',
  'lang.hi': 'हिन्दी',
  'lang.itIT': 'Italiano',
  'lang.nlNL': 'Nederlands',
  'lang.thTH': 'ไทย',
  'lang.viVN': 'Tiếng Việt',
  'lang.idID': 'Bahasa Indonesia',
  'lang.trTR': 'Türkçe',
  'lang.plPL': 'Polski',
  'lang.ukUA': 'Українська',
  'theme.system': 'システム',
  'theme.dark': 'ダーク（エンジニア）',
  'theme.light': 'ライト',
}
const koKR = { ...enUS }
const frFR = { ...enUS }
const deDE = { ...enUS }
const esES = { ...enUS }
const ptBR = { ...enUS }
const ruRU = { ...enUS }
const ar = { ...enUS }
const hi = { ...enUS }
const itIT = { ...enUS }
const nlNL = { ...enUS }
const thTH = { ...enUS }
const viVN = { ...enUS }
const idID = { ...enUS }
const trTR = { ...enUS }
const plPL = { ...enUS }
const ukUA = { ...enUS }

const translations = {
  'zh-CN': zhCN,
  'zh-TW': zhTW,
  'en-US': enUS,
  'ja-JP': jaJP,
  'ko-KR': koKR,
  'fr-FR': frFR,
  'de-DE': deDE,
  'es-ES': esES,
  'pt-BR': ptBR,
  'ru-RU': ruRU,
  ar,
  hi,
  'it-IT': itIT,
  'nl-NL': nlNL,
  'th-TH': thTH,
  'vi-VN': viVN,
  'id-ID': idID,
  'tr-TR': trTR,
  'pl-PL': plPL,
  'uk-UA': ukUA,
}

const t = (key, fallback = '') => {
  const lang = uiLanguage.value || 'zh-CN'
  return translations[lang]?.[key] ?? translations['zh-CN']?.[key] ?? fallback ?? key
}

const tr = (text) => {
  const lang = uiLanguage.value || 'zh-CN'
  const key = String(text ?? '')
  return translations[lang]?.[key] ?? translations['zh-CN']?.[key] ?? key
}

const uiLabels = computed(() => ({
  manual: t('nav.manual'),
  scripts: t('nav.scripts'),
  proxy: t('nav.proxy'),
  protocols: t('nav.protocols'),
  settings: t('nav.settings'),
  workspace: t('nav.workspace'),
}))
const channelTab = ref('all')
const protocolTab = ref('all')
const protocolDialogOpen = ref(false)
const protocolDialogMode = ref('create')
const protocolEditing = ref(null)
const protocolDeleteOpen = ref(false)
const protocolDeleting = ref(null)
const protocolDraft = ref({
  id: '',
  key: '',
  name: '',
  desc: '',
  category: 'custom',
  status: 'custom',
})
const settingsGeneralRef = ref(null)
const settingsPluginsRef = ref(null)
const settingsRuntimeRef = ref(null)
const settingsLogsRef = ref(null)
const uiRuntime = useUiRuntimeStore()
const uiModalOpen = ref(false)
const appVersion = ref('')

const noPorts = computed(() => ports.value.length === 0)
const portOptionsList = computed(() => ports.value.map((item) => ({ label: item, value: item, icon: 'usb' })))

const quickCommands = ref([
  { id: 'qc_at_gmr', name: 'AT+GMR', payload: 'AT+GMR', mode: 'text', appendCR: true, appendLF: true },
  { id: 'qc_reset', name: 'RESET_DEVICE_01', payload: 'RESET_DEVICE_01', mode: 'text', appendCR: true, appendLF: true },
  { id: 'qc_wifi', name: 'GET_WIFI_STATUS', payload: 'GET_WIFI_STATUS', mode: 'text', appendCR: true, appendLF: true },
  { id: 'qc_ping', name: 'PING_SERVER', payload: 'PING_SERVER', mode: 'text', appendCR: true, appendLF: true },
])
const QUICK_PAYLOAD_LIMIT = 256
const quickDialogOpen = ref(false)
const quickDialogMode = ref('create')
const quickEditingId = ref('')
const quickDeleteOpen = ref(false)
const quickDeleting = ref(null)
const quickDraft = ref({
  name: '',
  payload: '',
  mode: 'text',
  appendCR: true,
  appendLF: true,
})

const channels = ref([])
const channelCards = computed(() => {
  return channels.value.map((channel) => {
    const type = channel.type || 'unknown'
    const status = channel.status || 'disconnected'
    const statusMap = {
      connected: { text: t('status.connected'), className: 'status-ok' },
      connecting: { text: t('status.connecting'), className: 'status-warn' },
      error: { text: t('status.error'), className: 'status-error' },
      disconnected: { text: t('status.disconnected'), className: 'status-idle' },
      idle: { text: tr('空闲'), className: 'status-idle' },
    }
    const statusInfo = statusMap[status] || statusMap.disconnected
    const isSerial = type === 'serial'
    const isTcpClient = type === 'tcp-client'
    const name = isSerial ? tr('串口通道') : isTcpClient ? tr('TCP 客户端') : tr('TCP 服务端')
    const details = isSerial
      ? [channel.port || '--', channel.baud ? `${channel.baud} bps` : '--']
      : [channel.host || channel.address || '--', channel.port ? `${tr('端口')}: ${channel.port}` : '--']
    const traffic = `TX: ${formatBytes(channel.tx_bytes || 0)} / RX: ${formatBytes(channel.rx_bytes || 0)}`
    return {
      id: channel.id || `${type}:${details[0]}`,
      name,
      type: isSerial ? 'Serial' : isTcpClient ? 'TCP Client' : 'TCP Server',
      category: type,
      statusText: statusInfo.text,
      statusClass: statusInfo.className,
      details,
      traffic,
      error: channel.error || '',
    }
  })
})

const protocolCards = ref([])

const isConnected = computed(() => connectionInfo.value.state === 'connected')

const sliceTail = (items, limit) => {
  if (!Array.isArray(items)) return []
  if (!limit || items.length <= limit) return items
  return items.slice(items.length - limit)
}

const visibleCommLogs = computed(() => filterCommLogs(commLogs.value, logTab.value, logKeyword.value))
const renderedCommLogs = computed(() => sliceTail(commLogs.value, MAX_RENDER_LOGS))
const renderedVisibleCommLogs = computed(() => sliceTail(visibleCommLogs.value, MAX_RENDER_LOGS))
const renderedScriptLogs = computed(() => sliceTail(scriptLogs.value, MAX_RENDER_LOGS))
const scriptVariables = computed(() => scriptVariablesList.value)
const scriptErrorCount = computed(
  () => scriptLogs.value.filter((line) => String(line.text || '').toLowerCase().includes('[error]')).length
)
const scriptStepTotal = computed(() => countScriptSteps(yamlText.value))
const scriptStepIndex = computed(() => {
  if (!scriptStepTotal.value) return 0
  return Math.max(
    0,
    Math.min(scriptStepTotal.value, Math.round((scriptProgress.value / 100) * scriptStepTotal.value))
  )
})
const scriptElapsedLabel = computed(() => formatElapsed(scriptElapsedMs.value))
const scriptCanRun = computed(() => !scriptRunning.value && yamlText.value.trim().length > 0)
const scriptCanStop = computed(() => scriptRunning.value)
const scriptStatusLabel = computed(() => {
  if (scriptRunning.value) {
    return scriptState.value ? `${tr('运行中')} ${scriptState.value}` : tr('运行中')
  }
  return tr('空闲')
})
const scriptStatusClass = computed(() => (scriptRunning.value ? 'running' : 'idle'))
const quickPayloadCount = computed(() => countQuickPayload(quickDraft.value.payload, quickDraft.value.mode))
const languageOptions = computed(() => [
  { value: 'zh-CN', label: t('lang.zhCN') },
  { value: 'zh-TW', label: t('lang.zhTW') },
  { value: 'en-US', label: t('lang.enUS') },
  { value: 'ja-JP', label: t('lang.jaJP') },
  { value: 'ko-KR', label: t('lang.koKR') },
  { value: 'fr-FR', label: t('lang.frFR') },
  { value: 'de-DE', label: t('lang.deDE') },
  { value: 'es-ES', label: t('lang.esES') },
  { value: 'pt-BR', label: t('lang.ptBR') },
  { value: 'ru-RU', label: t('lang.ruRU') },
  { value: 'ar', label: t('lang.ar') },
  { value: 'hi', label: t('lang.hi') },
  { value: 'it-IT', label: t('lang.itIT') },
  { value: 'nl-NL', label: t('lang.nlNL') },
  { value: 'th-TH', label: t('lang.thTH') },
  { value: 'vi-VN', label: t('lang.viVN') },
  { value: 'id-ID', label: t('lang.idID') },
  { value: 'tr-TR', label: t('lang.trTR') },
  { value: 'pl-PL', label: t('lang.plPL') },
  { value: 'uk-UA', label: t('lang.ukUA') },
])
const themeOptions = computed(() => [
  { value: 'system', label: t('theme.system') },
  { value: 'dark', label: t('theme.dark') },
  { value: 'light', label: t('theme.light') },
])
const appVersionLabel = computed(() => appVersion.value || 'v0.0.0')

const filteredChannelCards = computed(() => {
  if (channelTab.value === 'all') return channelCards.value
  return channelCards.value.filter((card) => card.category === channelTab.value)
})
const filteredProtocolCards = computed(() => {
  if (protocolTab.value === 'all') return protocolCards.value
  return protocolCards.value.filter((card) => card.category === protocolTab.value)
})

function setSettingsTab(tab) {
  settingsTab.value = tab
}

const manualViewBindings = {
  connectionInfo,
  isConnected,
  isConnecting,
  selectedPort,
  portOptionsList,
  portPlaceholder,
  noPorts,
  sendMode,
  sendText,
  sendHex,
  appendCR,
  appendLF,
  loopSend,
  displayMode,
  quickCommands,
  logTab,
  logKeyword,
  visibleCommLogs,
  renderedCommLogs,
  renderedVisibleCommLogs,
  formatTime,
  formatPayload,
  commPaused,
  clearCommLogs,
  toggleCommPaused,
  exportCommLogs,
  quickDialogOpen,
  quickDialogMode,
  quickDraft,
  quickPayloadCount,
  quickPayloadLimit: QUICK_PAYLOAD_LIMIT,
  openQuickCommandDialog,
  closeQuickCommandDialog,
  saveQuickCommand,
  quickDeleteOpen,
  quickDeleting,
  openQuickDeleteDialog,
  closeQuickDeleteDialog,
  confirmQuickDelete,
  addQuickCommand,
  editQuickCommand,
  removeQuickCommand,
  selectPort,
  refreshPorts,
  openChannelSettings,
  disconnect,
  connectSerial,
  sendPayload,
  sendQuickCommand,
}

const scriptsViewBindings = {
  scriptFileName,
  scriptFilePath,
  loadYaml,
  saveYaml,
  yamlFileInputRef,
  handleYamlFile,
  yamlCollapsed,
  toggleYamlCollapsed,
  copyYaml,
  searchYaml,
  yamlEditorRef,
  scriptStatusClass,
  scriptRunning,
  scriptStatusLabel,
  scriptCanRun,
  scriptCanStop,
  runScript,
  stopScript,
  scriptState,
  scriptStepIndex,
  scriptStepTotal,
  scriptProgress,
  scriptElapsedLabel,
  scriptErrorCount,
  scriptVariables,
  refreshScriptVariables,
  clearScriptLogs,
  scrollScriptLogsToBottom,
  renderedScriptLogs,
  scriptLogRef,
}

provide('manualView', manualViewBindings)
provide('scriptsView', scriptsViewBindings)
provide('bridge', bridge)
provide('t', t)
provide('tr', tr)

let scriptTimer = null
let yamlEditor = null
let yamlEditorUpdating = false
let scriptVarTimer = null
let channelRefreshTimer = null
let snapPreviewRaf = 0
let pendingSnapPreview = null
let attachedBridge = null
const SCROLL_LOCK_SELECTORS = [
  '.page',
  '.modal-body',
  '.log-stream',
  '.quick-list',
  '.sidebar-nav',
  '.select-menu',
  '.proxy-modal-list',
]
let scrollLockSnapshot = []

function preventScroll(event) {
  if (!event) return
  event.preventDefault()
}

function lockPageScroll() {
  const selector = SCROLL_LOCK_SELECTORS.join(', ')
  const nodes = document.querySelectorAll(selector)
  scrollLockSnapshot = Array.from(nodes).map((node) => {
    return { el: node, top: node.scrollTop || 0 }
  })
  document.addEventListener('wheel', preventScroll, { passive: false })
  document.addEventListener('touchmove', preventScroll, { passive: false })
}

function unlockPageScroll() {
  scrollLockSnapshot.forEach((item) => {
    if (item.el) {
      item.el.scrollTop = item.top
    }
  })
  scrollLockSnapshot = []
  document.removeEventListener('wheel', preventScroll)
  document.removeEventListener('touchmove', preventScroll)
}

function filterCommLogs(lines, tab, keyword) {
  if (tab === 'tcp') return []
  const needle = String(keyword || '').trim().toLowerCase()
  if (!needle) return lines
  return lines.filter((line) => {
    const text = String(line.text || '').toLowerCase()
    const hex = String(line.hex || '').toLowerCase()
    return text.includes(needle) || hex.includes(needle)
  })
}

function formatTime(ts) {
  const date = new Date((ts || 0) * 1000)
  const pad = (value, len = 2) => String(value).padStart(len, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(
    date.getMilliseconds(),
    3
  )}`
}

function formatElapsed(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  const tenths = Math.floor((ms % 1000) / 100)
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${tenths}`
}

function formatBytes(value) {
  const bytes = Number(value) || 0
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} KB`
  const mb = kb / 1024
  if (mb < 1024) return `${mb.toFixed(1)} MB`
  const gb = mb / 1024
  return `${gb.toFixed(1)} GB`
}

function countScriptSteps(text) {
  if (!text) return 0
  const matches = text.match(/^\s*-\s*step\s*:/gm)
  return matches ? matches.length : 0
}

function parseScriptVariables(text) {
  if (!text) return []
  const lines = text.split(/\r?\n/)
  const vars = []
  let inVars = false
  for (const line of lines) {
    if (!inVars) {
      if (/^\s*variables\s*:\s*$/.test(line)) {
        inVars = true
      }
      continue
    }
    if (!line.trim()) continue
    if (!/^\s+/.test(line)) break
    const match = line.match(/^\s+([A-Za-z0-9_-]+)\s*:\s*(.*)$/)
    if (!match) continue
    let value = match[2].trim()
    value = value.replace(/^['"]|['"]$/g, '')
    vars.push({ name: match[1], value })
  }
  return vars
}

function initYamlEditor() {
  if (!yamlEditorRef.value || yamlEditor) return
  if (yamlEditorRef.value) {
    yamlEditorRef.value.style.height = yamlCollapsed.value ? '360px' : '640px'
  }
  const theme = EditorView.theme(
    {
      '&': {
        height: '100%',
        backgroundColor: '#fafafa',
        fontFamily:
          'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
        fontSize: '13px',
      },
      '.cm-scroller': {
        overflow: 'auto',
      },
      '.cm-content': {
        padding: '16px',
      },
      '.cm-gutters': {
        backgroundColor: '#f8fafc',
        borderRight: '1px solid #e2e8f0',
      },
      '.cm-lineNumbers': {
        color: '#94a3b8',
      },
      '.cm-activeLine': {
        backgroundColor: '#eef2ff',
      },
      '.cm-activeLineGutter': {
        backgroundColor: '#e0e7ff',
      },
    },
    { dark: false }
  )
  const indentPlugin = ViewPlugin.fromClass(
    class {
      constructor(view) {
        this.decorations = this.build(view)
      }
      update(update) {
        if (update.docChanged || update.viewportChanged) {
          this.decorations = this.build(update.view)
        }
      }
      build(view) {
        const builder = new RangeSetBuilder()
        for (const { from, to } of view.visibleRanges) {
          let pos = from
          while (pos <= to) {
            const line = view.state.doc.lineAt(pos)
            const indentMatch = line.text.match(/^\s+/)
            const indent = indentMatch ? indentMatch[0].length : 0
            const level = Math.min(5, Math.floor(indent / 2) + 1)
            builder.add(line.from, line.from, Decoration.line({ class: `yaml-indent-${level}` }))
            pos = line.to + 1
          }
        }
        return builder.finish()
      }
    },
    {
      decorations: (value) => value.decorations,
    }
  )
  const state = EditorState.create({
    doc: yamlText.value,
    extensions: [
      basicSetup,
      yamlLanguage(),
      syntaxHighlighting(
        HighlightStyle.define([
          { tag: tags.keyword, color: '#1d4ed8' },
          { tag: tags.atom, color: '#1d4ed8' },
          { tag: tags.string, color: '#16a34a' },
          { tag: tags.number, color: '#f97316' },
          { tag: tags.bool, color: '#1d4ed8' },
          { tag: tags.comment, color: '#94a3b8', fontStyle: 'italic' },
          { tag: tags.punctuation, color: '#64748b' },
        ])
      ),
      theme,
      EditorView.lineWrapping,
      indentPlugin,
      EditorView.updateListener.of((update) => {
        if (!update.docChanged) return
        yamlEditorUpdating = true
        yamlText.value = update.state.doc.toString()
        yamlEditorUpdating = false
      }),
    ],
  })
  yamlEditor = new EditorView({
    state,
    parent: yamlEditorRef.value,
  })
}

function destroyYamlEditor() {
  if (!yamlEditor) return
  yamlEditor.destroy()
  yamlEditor = null
}

function toggleYamlCollapsed() {
  yamlCollapsed.value = !yamlCollapsed.value
}

function formatPayload(item) {
  if (!item) return ''
  if (displayMode.value === 'hex' && item.hex) return item.hex
  return item.text || item.hex || ''
}

function parseBridgePayload(payload) {
  if (typeof payload !== 'string') return payload
  try {
    return JSON.parse(payload)
  } catch (err) {
    return { text: String(payload) }
  }
}

function scheduleLogFlush() {
  if (logFlushHandle) return
  logFlushHandle = window.requestAnimationFrame(() => {
    logFlushHandle = 0
    flushLogs()
  })
}

function formatCaptureTime(ts) {
  const date = new Date((ts || 0) * 1000)
  const pad = (value, length = 2) => String(value).padStart(length, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}.${pad(
    date.getMilliseconds(),
    3
  )}`
}

function mapCaptureFrame(payload) {
  if (!payload || typeof payload !== 'object') return null
  const protocol = payload.protocol || {}
  const unknown = Boolean(protocol.unknown)
  const direction = payload.direction || 'RX'
  const tone = unknown ? 'red' : direction === 'TX' ? 'blue' : 'green'
  return {
    id: payload.id || `cap-${Date.now()}`,
    direction,
    time: formatCaptureTime(payload.timestamp || Date.now() / 1000),
    size: payload.length || 0,
    note: payload.raw_hex || '',
    summary: payload.summary || '',
    summaryText: payload.summary || '',
    tone,
    warn: unknown,
    channel: payload.channel || '',
    baud: payload.baud || '',
    protocolLabel: protocol.name || (unknown ? 'Unknown' : ''),
    protocolType: unknown
      ? 'unknown'
      : (protocol.name || '').toLowerCase().includes('modbus')
        ? 'modbus'
        : 'custom',
    protocolTooltip: protocol.name ? `${protocol.name}${protocol.version ? ` ${protocol.version}` : ''}` : '',
    hexDump: payload.hex_dump || null,
    tree: payload.tree || [],
  }
}

function ingestCaptureFrame(payload) {
  const frame = mapCaptureFrame(payload)
  if (!frame) return
  captureFrames.value.push(frame)
  if (captureFrames.value.length > MAX_CAPTURE_FRAMES) {
    captureFrames.value.splice(0, captureFrames.value.length - MAX_CAPTURE_FRAMES)
  }
  captureMeta.value.totalFrames += 1
  captureMeta.value.rangeEnd = captureMeta.value.totalFrames
  captureMeta.value.rangeStart = Math.max(1, captureMeta.value.totalFrames - captureFrames.value.length + 1)
  captureMeta.value.bufferUsed = Math.min(
    100,
    Math.round((captureFrames.value.length / MAX_CAPTURE_FRAMES) * 100)
  )
  if (payload && payload.channel) {
    captureMeta.value.channel = payload.channel
  }
}

function flushLogs() {
  if (commLogBuffer.length) {
    const batch = commLogBuffer.splice(0, commLogBuffer.length)
    commLogs.value.push(...batch)
    if (commLogs.value.length > MAX_COMM_LOGS) {
      commLogs.value.splice(0, commLogs.value.length - MAX_COMM_LOGS)
    }
  }
  if (scriptLogBuffer.length) {
    scriptLogs.value.push(...scriptLogBuffer.splice(0, scriptLogBuffer.length))
    if (scriptLogs.value.length > MAX_SCRIPT_LOGS) {
      scriptLogs.value.splice(0, scriptLogs.value.length - MAX_SCRIPT_LOGS)
    }
  }
}

function addCommLog(kind, payload) {
  if (commPaused.value) return
  if (!payload || typeof payload !== 'object') {
    payload = { text: String(payload || ''), hex: '', ts: Date.now() / 1000 }
  } else if (!payload.text && !payload.hex) {
    payload = { text: JSON.stringify(payload), hex: '', ts: payload.ts || Date.now() / 1000 }
  }
  commLogBuffer.push({
    id: `c${commLogSeq++}`,
    kind,
    text: payload.text || '',
    hex: payload.hex || '',
    ts: payload.ts || Date.now() / 1000,
  })
  scheduleLogFlush()
}

function emitStatus(text, ts) {
  const message = String(text || '')
  if (!message || message === lastStatusText) return
  lastStatusText = message
  hasStatusActivity = true
  addCommLog('STATUS', { text: message, ts })
}

function addScriptLog(line) {
  const text = String(line || '')
  scriptLogBuffer.push({ id: `s${scriptLogSeq++}`, text })
  scheduleLogFlush()
  if (
    text.includes('Script finished') ||
    text.includes('Script stopped') ||
    text.toLowerCase().includes('[error]')
  ) {
    scriptRunning.value = false
    scriptState.value = 'idle'
  }
}

function clearCommLogs() {
  commLogs.value = []
  commLogBuffer.length = 0
}

function toggleCommPaused() {
  commPaused.value = !commPaused.value
}

function formatCommLine(item) {
  if (!item) return ''
  const ts = item.ts ? formatTime(item.ts) : ''
  const kind = item.kind || ''
  const payload = formatPayload(item).replace(/\r?\n/g, '\\n')
  return `${ts}\t${kind}\t${payload}`
}

function exportCommLogs() {
  const lines = commLogs.value.map((item) => formatCommLine(item)).filter(Boolean)
  const payload = lines.join('\n')
  const name = `io_logs_${new Date().toISOString().replace(/[:.]/g, '-')}.log`
  const blob = new Blob([payload], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function normalizeQuickCommands(list) {
  if (!Array.isArray(list)) return quickCommands.value
  const normalized = []
  list.forEach((item, index) => {
    if (!item) return
    if (typeof item === 'string') {
      normalized.push({
        id: `qc_${index}`,
        name: item,
        payload: item,
        mode: 'text',
        appendCR: true,
        appendLF: true,
      })
      return
    }
    const name = String(item.name || item.payload || '').trim()
    const payload = String(item.payload || item.name || '').trim()
    if (!name || !payload) return
    normalized.push({
      id: item.id || `qc_${index}`,
      name,
      payload,
      mode: item.mode === 'hex' ? 'hex' : 'text',
      appendCR: item.appendCR ?? true,
      appendLF: item.appendLF ?? true,
    })
  })
  return normalized.length ? normalized : quickCommands.value
}

function addQuickCommand() {
  openQuickCommandDialog()
}

function editQuickCommand(cmd) {
  openQuickCommandDialog(cmd)
}

function removeQuickCommand(cmd) {
  openQuickDeleteDialog(cmd)
}

function openQuickDeleteDialog(cmd) {
  if (!cmd) return
  quickDeleting.value = cmd
  quickDeleteOpen.value = true
}

function closeQuickDeleteDialog() {
  quickDeleteOpen.value = false
  quickDeleting.value = null
}

function confirmQuickDelete() {
  if (!quickDeleting.value) return
  quickCommands.value = quickCommands.value.filter((item) => item.id !== quickDeleting.value.id)
  closeQuickDeleteDialog()
}

function openQuickCommandDialog(cmd) {
  if (cmd) {
    quickDialogMode.value = 'edit'
    quickEditingId.value = cmd.id
    quickDraft.value = {
      name: cmd.name || '',
      payload: cmd.payload || cmd.name || '',
      mode: cmd.mode === 'hex' ? 'hex' : 'text',
      appendCR: cmd.appendCR ?? true,
      appendLF: cmd.appendLF ?? true,
    }
  } else {
    quickDialogMode.value = 'create'
    quickEditingId.value = ''
    quickDraft.value = {
      name: '',
      payload: '',
      mode: sendMode.value === 'hex' ? 'hex' : 'text',
      appendCR: appendCR.value,
      appendLF: appendLF.value,
    }
  }
  quickDialogOpen.value = true
}

function closeQuickCommandDialog() {
  quickDialogOpen.value = false
}

function saveQuickCommand() {
  const name = String(quickDraft.value.name || '').trim()
  const payload = String(quickDraft.value.payload || '').trim()
  if (!name || !payload) {
    window.alert(tr('请输入指令名称和内容'))
    return
  }
  const record = {
    name,
    payload: quickDraft.value.payload,
    mode: quickDraft.value.mode === 'hex' ? 'hex' : 'text',
    appendCR: quickDraft.value.appendCR ?? true,
    appendLF: quickDraft.value.appendLF ?? true,
  }
  if (quickDialogMode.value === 'edit' && quickEditingId.value) {
    const target = quickCommands.value.find((item) => item.id === quickEditingId.value)
    if (target) {
      Object.assign(target, record)
    } else {
      quickCommands.value.push({
        id: quickEditingId.value,
        ...record,
      })
    }
  } else {
    quickCommands.value.push({
      id: `qc_${Date.now()}_${Math.random().toString(16).slice(2, 6)}`,
      ...record,
    })
  }
  closeQuickCommandDialog()
}

function countQuickPayload(payload, mode) {
  const value = String(payload || '')
  if (mode === 'hex') {
    const cleaned = value.replace(/[^0-9a-fA-F]/g, '')
    return Math.floor(cleaned.length / 2)
  }
  return value.length
}

function addCommBatch(batch) {
  if (commPaused.value) return
  batch = parseBridgePayload(batch)
  if (!Array.isArray(batch)) return
  for (const item of batch) {
    if (!item) continue
    const kind = item.kind || 'RX'
    if (kind === 'FRAME') {
      addCommLog('FRAME', { text: JSON.stringify(item.payload), ts: item.ts })
    } else {
      let payload = item.payload || {}
      if (
        payload &&
        typeof payload === 'object' &&
        !payload.text &&
        !payload.hex &&
        (item.text || item.hex)
      ) {
        payload = { text: item.text || '', hex: item.hex || '', ts: item.ts || payload.ts }
      }
      if (payload && typeof payload === 'object' && !payload.text && !payload.hex) {
        payload = { text: JSON.stringify(item), ts: item.ts || payload.ts }
      }
      addCommLog(kind, payload)
    }
  }
}

function withResult(value, handler) {
  if (value && typeof value.then === 'function') {
    value.then(handler)
  } else {
    handler(value)
  }
}

function refreshPorts() {
  if (!bridge.value) return
  withResult(bridge.value.list_ports(), (items) => {
    ports.value = items || []
    if (!selectedPort.value && ports.value.length) {
      selectedPort.value = ports.value[0]
    }
  })
}

function setChannels(items) {
  channels.value = Array.isArray(items) ? items : []
  const primary = channels.value[0]
  if (!primary) return
  if (primary.status === 'connected') {
    const target = primary.address || primary.port || primary.type || ''
    emitStatus(`Connected: ${target}`, Date.now() / 1000)
    connectionInfo.value = {
      state: 'connected',
      detail: primary.address || primary.port || primary.type || '',
    }
    hasStatusActivity = true
    isConnecting.value = false
    return
  }
  if (primary.status === 'error') {
    emitStatus(`Error: ${primary.error || ''}`, Date.now() / 1000)
    connectionInfo.value = { state: 'error', detail: primary.error || '' }
    isConnecting.value = false
    return
  }
}

function refreshChannels() {
  if (!bridge.value || !bridge.value.list_channels) return
  withResult(bridge.value.list_channels(), (items) => {
    setChannels(items)
  })
}


function scheduleChannelRefresh() {
  if (channelRefreshTimer) return
  channelRefreshTimer = window.setTimeout(() => {
    channelRefreshTimer = null
    refreshChannels()
  }, 150)
}

function protocolCategory(key) {
  const name = String(key || "").toLowerCase()
  if (name.startsWith("modbus_")) return "modbus"
  if (name.includes("tcp")) return "tcp"
  return "custom"
}

function prettyProtocolName(key, fallback) {
  const value = String(key || "").trim()
  if (!value) return fallback || tr('协议')
  const parts = value.split("_").map((part) => {
    const upper = part.toUpperCase()
    if (["RTU", "TCP", "SCPI", "AT", "XMODEM", "YMODEM"].includes(upper)) return upper
    if (upper.length <= 2) return upper
    return part.charAt(0).toUpperCase() + part.slice(1)
  })
  return parts.join(" ")
}

function protocolStatusInfo(status) {
  if (status === "available") {
    return { text: tr('可用'), className: 'badge-green' }
  }
  if (status === "custom") {
    return { text: tr('自定义'), className: 'badge-blue' }
  }
  if (status === "disabled") {
    return { text: tr('已禁用'), className: 'badge-gray' }
  }
  return { text: status || tr('未知'), className: 'badge-gray' }
}

function setProtocols(items) {
  const list = Array.isArray(items) ? items : []
  protocolCards.value = list.map((item) => {
    const key = String(item.key || item.id || "")
    const driver = String(item.driver || "")
    const name = String(item.name || "")
    const category = String(item.category || protocolCategory(key))
    const status = String(item.status || "available")
    const source = String(item.source || "builtin")
    const desc = String(item.desc || "")
    const statusInfo = protocolStatusInfo(status)
    return {
      id: key || driver || Math.random().toString(36).slice(2),
      key,
      name: name || prettyProtocolName(key, driver),
      driver,
      category,
      desc,
      statusText: statusInfo.text,
      statusClass: statusInfo.className,
      status,
      source,
      rows: [
        { label: tr('键名'), value: key || '--' },
        { label: tr('驱动'), value: driver || '--' },
        { label: tr('分类'), value: category || '--' },
      ],
    }
  })
}

function refreshProtocols() {
  if (!bridge.value || !bridge.value.list_protocols) return
  withResult(bridge.value.list_protocols(), (items) => {
    setProtocols(items)
  })
}

function resetProtocolDraft() {
  protocolDraft.value = {
    id: "",
    key: "",
    name: "",
    desc: "",
    category: "custom",
    status: "custom",
  }
}

function openCreateProtocol() {
  protocolDialogMode.value = "create"
  protocolEditing.value = null
  resetProtocolDraft()
  protocolDialogOpen.value = true
}

function openProtocolDetails(card) {
  if (!card) return
  protocolEditing.value = card
  protocolDialogMode.value = card.source === "custom" ? "edit" : "view"
  protocolDraft.value = {
    id: card.id || "",
    key: card.key || "",
    name: card.name || "",
    desc: card.desc || "",
    category: card.category || "custom",
    status: card.status || "available",
  }
  protocolDialogOpen.value = true
}

function closeProtocolDialog() {
  protocolDialogOpen.value = false
}

function saveProtocol() {
  if (!bridge.value) {
    protocolDialogOpen.value = false
    return
  }
  const payload = {
    id: protocolDraft.value.id,
    key: protocolDraft.value.key,
    name: protocolDraft.value.name,
    desc: protocolDraft.value.desc,
    category: protocolDraft.value.category,
    status: protocolDraft.value.status,
  }
  if (protocolDialogMode.value === "create") {
    if (!bridge.value.create_protocol) return
    withResult(bridge.value.create_protocol(payload), () => {
      refreshProtocols()
      protocolDialogOpen.value = false
    })
    return
  }
  if (protocolDialogMode.value === "edit") {
    if (!bridge.value.update_protocol) return
    withResult(bridge.value.update_protocol(payload), () => {
      refreshProtocols()
      protocolDialogOpen.value = false
    })
    return
  }
  protocolDialogOpen.value = false
}

function openProtocolDelete(card) {
  if (!card || card.source !== "custom") return
  protocolDeleting.value = card
  protocolDeleteOpen.value = true
}

function closeProtocolDelete() {
  protocolDeleteOpen.value = false
  protocolDeleting.value = null
}

function confirmProtocolDelete() {
  if (!bridge.value || !bridge.value.delete_protocol || !protocolDeleting.value) {
    closeProtocolDelete()
    return
  }
  const id = protocolDeleting.value.id
  withResult(bridge.value.delete_protocol(id), () => {
    refreshProtocols()
    closeProtocolDelete()
  })
}


function handleChannelRefresh() {
  refreshChannels()
  refreshPorts()
}

function handleNewChannel() {
  channelDialogMode.value = 'create'
  channelType.value = 'serial'
  channelName.value = ''
  channelPort.value = selectedPort.value || ports.value[0] || ''
  channelBaud.value = Number(defaultBaud.value || 115200)
  channelDataBits.value = '8'
  channelParity.value = defaultParity.value || 'none'
  channelStopBits.value = defaultStopBits.value || '1'
  channelFlowControl.value = 'none'
  channelReadTimeout.value = 1000
  channelWriteTimeout.value = 1000
  channelHost.value = tcpHost.value || '127.0.0.1'
  channelTcpPort.value = Number(tcpPort.value || 502)
  channelAutoConnect.value = !!autoConnectOnStart.value
  channelDialogOpen.value = true
}

function openChannelSettings() {
  handleNewChannel()
  channelDialogMode.value = 'serial'
  channelType.value = 'serial'
}

function closeChannelDialog() {
  channelDialogOpen.value = false
}

function submitChannelDialog() {
  if (!bridge.value) return
  if (channelType.value === 'serial') {
    if (channelAutoConnect.value) {
      bridge.value.connect_serial(channelPort.value, Number(channelBaud.value || 115200))
    }
  } else if (channelType.value === 'tcp') {
    if (channelAutoConnect.value) {
      bridge.value.connect_tcp(channelHost.value, Number(channelTcpPort.value || 502))
    }
  }
  channelDialogOpen.value = false
}

function connectSerial() {
  if (!bridge.value) return
  if (isConnecting.value || isConnected.value) return
  isConnecting.value = true
  bridge.value.connect_serial(selectedPort.value, Number(baud.value))
}

function connectTcp() {
  if (!bridge.value) return
  if (isConnecting.value || isConnected.value) return
  isConnecting.value = true
  bridge.value.connect_tcp(tcpHost.value, Number(tcpPort.value))
}

function connectPrimary() {
  if (channelMode.value === 'tcp') {
    connectTcp()
  } else {
    connectSerial()
  }
}

function disconnect() {
  if (!bridge.value) return
  bridge.value.disconnect()
}

function applyLineEndings(text, cr = appendCR.value, lf = appendLF.value) {
  let payload = text
  if (cr) payload += '\r'
  if (lf) payload += '\n'
  return payload
}

function applyHexLineEndings(text, cr = appendCR.value, lf = appendLF.value) {
  const parts = text.trim().split(/\\s+/).filter(Boolean)
  if (cr) parts.push('0D')
  if (lf) parts.push('0A')
  return parts.join(' ')
}

function sendAscii() {
  if (!bridge.value || !sendText.value) return
  const payload = applyLineEndings(sendText.value)
  bridge.value.send_text(payload)
}

function sendHexData() {
  if (!bridge.value || !sendHex.value) return
  const payload = applyHexLineEndings(sendHex.value)
  bridge.value.send_hex(payload)
}

function sendPayload() {
  if (sendMode.value === 'hex') {
    sendHexData()
  } else {
    sendAscii()
  }
}

function sendQuickCommand(cmd) {
  if (!cmd) return
  const payload = typeof cmd === 'string' ? cmd : cmd.payload || cmd.name || ''
  if (!payload) return
  const mode = typeof cmd === 'string' ? 'text' : cmd.mode || 'text'
  const cr = typeof cmd === 'string' ? appendCR.value : cmd.appendCR ?? appendCR.value
  const lf = typeof cmd === 'string' ? appendLF.value : cmd.appendLF ?? appendLF.value
  if (mode === 'hex') {
    sendMode.value = 'hex'
    sendHex.value = payload
    if (!bridge.value) return
    const data = applyHexLineEndings(payload, cr, lf)
    bridge.value.send_hex(data)
    return
  }
  sendMode.value = 'text'
  sendText.value = payload
  if (!bridge.value) return
  const data = applyLineEndings(payload, cr, lf)
  bridge.value.send_text(data)
}

async function openUiYamlModal() {
  if (!uiModalOpen.value) {
    uiModalOpen.value = true
  }
  uiRuntime.yamlText = yamlText.value
  await uiRuntime._parseWithBridge()
}

function closeUiYamlModal() {
  uiModalOpen.value = false
}

function runScript() {
  if (!bridge.value) return
  const payload = yamlText.value.trim()
  if (!payload) {
    addScriptLog('[WARN] YAML is empty, abort run.')
    return
  }
  scriptRunning.value = true
  scriptState.value = 'starting'
  scriptStartMs.value = Date.now()
  scriptElapsedMs.value = 0
  scriptProgress.value = 0
  openUiYamlModal()
  bridge.value.run_script(payload)
}

function stopScript() {
  if (!bridge.value) return
  scriptState.value = 'stopping'
  bridge.value.stop_script()
  addScriptLog('[INFO] Stop requested.')
}

function loadYaml() {
  if (bridge.value && bridge.value.load_yaml) {
    withResult(bridge.value.load_yaml(), (payload) => {
      if (!payload || !payload.text) return
      yamlText.value = payload.text
      scriptFileName.value = payload.name || scriptFileName.value
      scriptFilePath.value = payload.path || scriptFilePath.value
      refreshScriptVariables()
      addScriptLog(`[INFO] Loaded: ${scriptFileName.value}`)
    })
    return
  }
  if (!yamlFileInputRef.value) return
  yamlFileInputRef.value.value = ''
  yamlFileInputRef.value.click()
}

function saveYaml() {
  const payload = yamlText.value.trim()
  if (!payload) {
    addScriptLog('[WARN] YAML is empty, not saved.')
    return
  }
  if (bridge.value && bridge.value.save_yaml) {
    withResult(bridge.value.save_yaml(payload, scriptFileName.value || 'workflow.yaml'), (info) => {
      if (!info) return
      if (info.name) scriptFileName.value = info.name
      if (info.path) scriptFilePath.value = info.path
      addScriptLog(`[INFO] Saved: ${scriptFileName.value}`)
    })
    return
  }
  const name = scriptFileName.value || 'script.yaml'
  const blob = new Blob([payload], { type: 'text/yaml' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
  addScriptLog(`[INFO] Saved: ${name}`)
}

function handleYamlFile(event) {
  const file = event && event.target && event.target.files ? event.target.files[0] : null
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    const text = typeof reader.result === 'string' ? reader.result : ''
    yamlText.value = text
    scriptFileName.value = file.name
    scriptFilePath.value = file.name
    refreshScriptVariables()
    addScriptLog(`[INFO] Loaded: ${file.name}`)
  }
  reader.readAsText(file)
}

async function copyYaml() {
  const payload = yamlText.value.trim()
  if (!payload) {
    addScriptLog('[WARN] YAML is empty, nothing to copy.')
    return
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(payload)
      addScriptLog('[INFO] YAML copied to clipboard.')
      return
    } catch (err) {
      addScriptLog('[WARN] Clipboard API failed, falling back.')
    }
  }
  const temp = document.createElement('textarea')
  temp.value = payload
  document.body.appendChild(temp)
  temp.select()
  document.execCommand('copy')
  temp.remove()
  addScriptLog('[INFO] YAML copied to clipboard.')
}

function searchYaml() {
  const keyword = window.prompt(tr('搜索关键词'))
  if (!keyword) return
  if (yamlEditor) {
    const doc = yamlEditor.state.doc.toString()
    const lower = doc.toLowerCase()
    const idx = lower.indexOf(keyword.toLowerCase())
    if (idx === -1) {
      addScriptLog(`[INFO] Not found: ${keyword}`)
      return
    }
    yamlEditor.dispatch({
      selection: { anchor: idx, head: idx + keyword.length },
      scrollIntoView: true,
    })
    return
  }
  const found = window.find(keyword)
  if (!found) {
    addScriptLog(`[INFO] Not found: ${keyword}`)
  }
}

function clearScriptLogs() {
  scriptLogs.value = []
  scriptLogBuffer.length = 0
}

function scrollScriptLogsToBottom() {
  if (!scriptLogRef.value) return
  const root = scriptLogRef.value.rootEl
  const el = root && root.value ? root.value : root
  if (!el) return
  el.scrollTop = el.scrollHeight
}

function refreshScriptVariables() {
  if (scriptVarTimer) {
    window.clearTimeout(scriptVarTimer)
    scriptVarTimer = null
  }
  scriptVariablesList.value = parseScriptVariables(yamlText.value)
}

function attachBridge(obj) {
  if (!obj || attachedBridge === obj) return
  attachedBridge = obj
  bridge.value = obj
  if (obj.get_app_version) {
    withResult(obj.get_app_version(), (value) => {
      if (value) {
        appVersion.value = String(value).trim()
      }
    })
  }
  if (obj.comm_rx && obj.comm_tx) {
    obj.comm_rx.connect((payload) => {
      const parsed = parseBridgePayload(payload)
      addCommLog('RX', parsed)
    })
    obj.comm_tx.connect((payload) => {
      const parsed = parseBridgePayload(payload)
      addCommLog('TX', parsed)
    })
  } else if (obj.comm_batch) {
    obj.comm_batch.connect((batch) => addCommBatch(batch))
  }
  if (obj.protocol_frame) {
    obj.protocol_frame.connect((payload) => {
      const ts = payload && payload.ts ? payload.ts : Date.now() / 1000
      addCommLog('FRAME', { text: JSON.stringify(payload), ts })
    })
  }
  if (obj.capture_frame) {
    obj.capture_frame.connect((payload) => {
      const ts = payload && payload.ts ? payload.ts : Date.now() / 1000
      addCommLog('CAPTURE', { text: JSON.stringify(payload), ts })
      ingestCaptureFrame(payload)
    })
  }
  obj.comm_status.connect((payload) => {
    const detail = payload && payload.payload !== undefined ? payload.payload : payload
    const ts = payload && payload.ts ? payload.ts : Date.now() / 1000
    isConnecting.value = false
    if (!detail) {
      const reason = payload && payload.reason ? String(payload.reason) : ''
      const message = reason ? `Disconnected: ${reason}` : 'Disconnected'
      if (hasStatusActivity || reason) {
        emitStatus(message, ts)
      }
      const nextInfo = { state: 'disconnected', detail: '' }
      connectionInfo.value = nextInfo
      scheduleChannelRefresh()
      return
    }
    if (typeof detail === 'string') {
      emitStatus(`Error: ${detail}`, ts)
      const nextInfo = { state: 'error', detail }
      connectionInfo.value = nextInfo
      scheduleChannelRefresh()
      return
    }
    if (detail && typeof detail === 'object') {
      const target = detail.address || detail.port || detail.type || ''
      emitStatus(`Connected: ${target}`, ts)
    }
    const nextInfo = {
      state: 'connected',
      detail: detail.address || detail.port || detail.type || '',
    }
    connectionInfo.value = nextInfo
    scheduleChannelRefresh()
  })
  obj.script_log.connect((line) => addScriptLog(line))
  obj.script_state.connect((state) => {
    scriptState.value = state
    if (state) {
      scriptRunning.value = true
    }
  })
  obj.script_progress.connect((value) => {
    scriptProgress.value = value
  })
  if (obj.channel_update) {
    obj.channel_update.connect((items) => {
      setChannels(items)
    })
  }
  refreshPorts()
  refreshChannels()
  refreshProtocols()
  loadSettings()
}

onMounted(() => {
  const timer = setInterval(() => {
    if (window.bridge) {
      attachBridge(window.bridge)
      clearInterval(timer)
    }
  }, 200)
  scriptTimer = window.setInterval(() => {
    if (scriptRunning.value && scriptStartMs.value) {
      scriptElapsedMs.value = Date.now() - scriptStartMs.value
    }
  }, 200)
  if (currentView.value === 'scripts') {
    nextTick(() => initYamlEditor())
  }
  window.addEventListener('keydown', handleGlobalKeydown)
  loadSettings()
})

onBeforeUnmount(() => {
  if (scriptTimer) {
    window.clearInterval(scriptTimer)
    scriptTimer = null
  }
  if (scriptVarTimer) {
    window.clearTimeout(scriptVarTimer)
    scriptVarTimer = null
  }
  if (logFlushHandle) {
    window.cancelAnimationFrame(logFlushHandle)
    logFlushHandle = 0
  }
  if (channelRefreshTimer) {
    window.clearTimeout(channelRefreshTimer)
    channelRefreshTimer = null
  }
  destroyYamlEditor()
  window.removeEventListener('keydown', handleGlobalKeydown)
})

watch(
  () => scriptLogs.value.length,
  async () => {
    if (!scriptAutoScroll.value) return
    await nextTick()
    scrollScriptLogsToBottom()
  }
)

watch(
  () => currentView.value,
  (value) => {
    if (value === 'scripts') {
      nextTick(() => initYamlEditor())
    } else {
      destroyYamlEditor()
    }
    if (value === 'protocols') {
      refreshProtocols()
    }
  }
)

watch(
  () => yamlCollapsed.value,
  (collapsed) => {
    if (yamlEditorRef.value) {
      yamlEditorRef.value.style.height = collapsed ? '360px' : '640px'
    }
  }
)

watch(
  () =>
    channelDialogOpen.value ||
    quickDialogOpen.value ||
    quickDeleteOpen.value ||
    protocolDialogOpen.value ||
    protocolDeleteOpen.value ||
    uiModalOpen.value,
  (open) => {
    document.body.classList.toggle('modal-open', open)
  }
)

watch(
  () => scriptRunning.value,
  (running) => {
    if (running && !uiModalOpen.value) {
      openUiYamlModal()
    }
  }
)

watch(
  () => yamlText.value,
  (value) => {
    if (!yamlEditor || yamlEditorUpdating) return
    const current = yamlEditor.state.doc.toString()
    if (value === current) return
    yamlEditor.dispatch({
      changes: { from: 0, to: current.length, insert: value },
    })
  }
)

watch(
  () => yamlText.value,
  (value) => {
    if (scriptVarTimer) {
      window.clearTimeout(scriptVarTimer)
    }
    scriptVarTimer = window.setTimeout(() => {
      scriptVariablesList.value = parseScriptVariables(value)
    }, 200)
  }
)

function armWindowMove(event) {
  if (!event) return
  dragArmed.value = true
  dragStarted.value = false
  dragStart.value = { x: event.screenX, y: event.screenY }
}

function maybeStartWindowMove(event) {
  if (!dragArmed.value || dragStarted.value || !event) return
  const dx = Math.abs(event.screenX - dragStart.value.x)
  const dy = Math.abs(event.screenY - dragStart.value.y)
  if (dx < 10 && dy < 10) return
  lockSidebarWidth()
  if (bridge.value) {
    if (bridge.value.window_start_move_at) {
      bridge.value.window_start_move_at(Math.round(event.screenX), Math.round(event.screenY))
    } else {
      bridge.value.window_start_move()
    }
  }
  dragStarted.value = true
  draggingWindow.value = true
  document.body.classList.add('dragging-window')
  lockPageScroll()
  snapPreview.value = ''
  attachDragListeners()
}

function minimizeWindow() {
  if (bridge.value) {
    bridge.value.window_minimize()
  }
}

function toggleMaximize() {
  if (bridge.value) {
    bridge.value.window_toggle_maximize()
  }
}

function closeWindow() {
  if (bridge.value) {
    bridge.value.window_close()
  }
}

function applyWindowSnap(event) {
  if (bridge.value && event && dragStarted.value) {
    bridge.value.window_apply_snap(Math.round(event.screenX), Math.round(event.screenY))
  }
  clearDragState()
}

function showSystemMenu(event) {
  if (bridge.value && event) {
    bridge.value.window_show_system_menu(Math.round(event.screenX), Math.round(event.screenY))
  }
}

function startResize(edge, event) {
  if (!bridge.value || !edge || !event) return
  document.body.classList.add('resizing')
  lockPageScroll()
  bridge.value.window_start_resize(edge)
}

function selectPort(item) {
  if (!item || noPorts.value) return
  selectedPort.value = item
  channelMode.value = 'serial'
}
function handleGlobalKeydown(event) {
  if (!event) return
  if (event.key === 'Escape') {
    if (channelDialogOpen.value) {
      closeChannelDialog()
    }
  }
}

function setChannelTab(tab) {
  channelTab.value = tab
}

function setProtocolTab(tab) {
  protocolTab.value = tab
}

const settingsDirty = computed(() => {
  if (!settingsSnapshot.value) return false
  return JSON.stringify(buildSettingsPayload()) !== JSON.stringify(settingsSnapshot.value)
})

function normalizeLanguage(value) {
  const raw = String(value || '')
  const lowered = raw.toLowerCase()
  const map = {
    'zh-cn': 'zh-CN',
    'zh-tw': 'zh-TW',
    'en-us': 'en-US',
    'ja-jp': 'ja-JP',
    'ko-kr': 'ko-KR',
    'fr-fr': 'fr-FR',
    'de-de': 'de-DE',
    'es-es': 'es-ES',
    'pt-br': 'pt-BR',
    'ru-ru': 'ru-RU',
    ar: 'ar',
    hi: 'hi',
    'it-it': 'it-IT',
    'nl-nl': 'nl-NL',
    'th-th': 'th-TH',
    'vi-vn': 'vi-VN',
    'id-id': 'id-ID',
    'tr-tr': 'tr-TR',
    'pl-pl': 'pl-PL',
    'uk-ua': 'uk-UA',
  }
  if (map[lowered]) return map[lowered]
  if (raw === '简体中文') return 'zh-CN'
  if (raw === '繁體中文' || raw === '繁体中文') return 'zh-TW'
  if (raw === 'English (US)') return 'en-US'
  return 'zh-CN'
}

function normalizeTheme(value) {
  const raw = String(value || '')
  const lowered = raw.toLowerCase()
  if (raw === 'system' || lowered === 'system' || raw === '系统默认') return 'system'
  if (raw === 'dark' || lowered === 'dark' || raw === '深色 (工程模式)') return 'dark'
  if (raw === 'light' || lowered === 'light' || raw === '浅色') return 'light'
  return 'light'
}

function buildSettingsPayload() {
  return {
    uiLanguage: uiLanguage.value,
    uiTheme: uiTheme.value,
    autoConnectOnStart: !!autoConnectOnStart.value,
    dslWorkspacePath: dslWorkspacePath.value,
    quickCommands: quickCommands.value,
    serial: {
      defaultBaud: Number(defaultBaud.value || 115200),
      defaultParity: defaultParity.value,
      defaultStopBits: defaultStopBits.value,
    },
    network: {
      tcpTimeoutMs: Number(tcpTimeoutMs.value || 0),
      tcpHeartbeatSec: Number(tcpHeartbeatSec.value || 0),
      tcpRetryCount: Number(tcpRetryCount.value || 0),
    },
  }
}

function normalizeSettings(payload) {
  const defaults = {
    uiLanguage: 'zh-CN',
    uiTheme: 'light',
    autoConnectOnStart: true,
    dslWorkspacePath: '/usr/local/protoflow/workflows',
    quickCommands: quickCommands.value,
    serial: {
      defaultBaud: 115200,
      defaultParity: 'none',
      defaultStopBits: '1',
    },
    network: {
      tcpTimeoutMs: 5000,
      tcpHeartbeatSec: 60,
      tcpRetryCount: 3,
    },
  }
  if (!payload || typeof payload !== 'object') return defaults
  return {
    ...defaults,
    ...payload,
    uiLanguage: normalizeLanguage(payload.uiLanguage),
    uiTheme: normalizeTheme(payload.uiTheme),
    serial: {
      ...defaults.serial,
      ...(payload.serial || {}),
    },
    network: {
      ...defaults.network,
      ...(payload.network || {}),
    },
  }
}

function applySettings(payload) {
  const normalized = normalizeSettings(payload)
  uiLanguage.value = normalized.uiLanguage
  uiTheme.value = normalized.uiTheme
  autoConnectOnStart.value = !!normalized.autoConnectOnStart
  dslWorkspacePath.value = normalized.dslWorkspacePath
  quickCommands.value = normalizeQuickCommands(normalized.quickCommands)
  defaultBaud.value = Number(normalized.serial.defaultBaud || 115200)
  defaultParity.value = normalized.serial.defaultParity || 'none'
  defaultStopBits.value = normalized.serial.defaultStopBits || '1'
  tcpTimeoutMs.value = Number(normalized.network.tcpTimeoutMs || 0)
  tcpHeartbeatSec.value = Number(normalized.network.tcpHeartbeatSec || 0)
  tcpRetryCount.value = Number(normalized.network.tcpRetryCount || 0)
  baud.value = Number(defaultBaud.value || 115200)
}

function loadSettings() {
  if (bridge.value && bridge.value.load_settings) {
    withResult(bridge.value.load_settings(), (payload) => {
      const normalized = normalizeSettings(payload)
      applySettings(normalized)
      settingsSnapshot.value = normalized
    })
    return
  }
  const normalized = normalizeSettings(null)
  applySettings(normalized)
  settingsSnapshot.value = normalized
}

function saveSettings() {
  const payload = buildSettingsPayload()
  settingsSaving.value = true
  const finalize = () => {
    settingsSnapshot.value = normalizeSettings(payload)
    settingsSaving.value = false
  }
  if (bridge.value && bridge.value.save_settings) {
    withResult(bridge.value.save_settings(payload), () => finalize())
  } else {
    finalize()
  }
}

function discardSettings() {
  if (!settingsSnapshot.value) return
  applySettings(settingsSnapshot.value)
}

function chooseDslWorkspace() {
  if (!bridge.value || !bridge.value.select_directory) return
  withResult(
    bridge.value.select_directory(tr('选择工作区'), dslWorkspacePath.value || ''),
    (value) => {
      if (value) {
        dslWorkspacePath.value = value
      }
    }
  )
}

function scheduleSnapPreview(event) {
  if (!event) return
  pendingSnapPreview = {
    x: event.clientX,
    y: event.clientY,
    screenX: event.screenX,
    screenY: event.screenY,
    buttons: event.buttons,
  }
  if (snapPreviewRaf) return
  snapPreviewRaf = window.requestAnimationFrame(() => {
    snapPreviewRaf = 0
    if (!pendingSnapPreview) return
    const payload = pendingSnapPreview
    pendingSnapPreview = null
    updateSnapPreview(payload)
  })
}

function updateSnapPreview(payload) {
  if (!draggingWindow.value || !payload) return
  if (payload.buttons !== 1) {
    applyWindowSnap(payload)
    return
  }
  if (!enableSnapPreview.value) {
    snapPreview.value = ''
    return
  }
  const margin = 24
  const x = payload.x
  const y = payload.y
  const width = window.innerWidth
  if (y <= margin) {
    snapPreview.value = 'max'
  } else if (x <= margin) {
    snapPreview.value = 'left'
  } else if (x >= width - margin) {
    snapPreview.value = 'right'
  } else {
    snapPreview.value = ''
  }
}

function handleDragEnd(event) {
  if (!draggingWindow.value) return
  applyWindowSnap(event)
}

function attachDragListeners() {
  window.addEventListener('mousemove', scheduleSnapPreview)
  window.addEventListener('mouseup', handleDragEnd)
  window.addEventListener('blur', handleDragCancel)
  document.addEventListener('visibilitychange', handleDragCancel)
}

function detachDragListeners() {
  window.removeEventListener('mousemove', scheduleSnapPreview)
  window.removeEventListener('mouseup', handleDragEnd)
  window.removeEventListener('blur', handleDragCancel)
  document.removeEventListener('visibilitychange', handleDragCancel)
}

function handleDragCancel() {
  clearDragState()
}

function clearDragState() {
  draggingWindow.value = false
  dragArmed.value = false
  dragStarted.value = false
  snapPreview.value = ''
  pendingSnapPreview = null
  unlockSidebarWidth()
  if (snapPreviewRaf) {
    window.cancelAnimationFrame(snapPreviewRaf)
    snapPreviewRaf = 0
  }
  document.body.classList.remove('dragging-window')
  document.body.classList.remove('resizing')
  unlockPageScroll()
  detachDragListeners()
}

function lockSidebarWidth() {
  const sidebar = sidebarRef.value
  if (!sidebar || !sidebar.getBoundingClientRect) return
  const width = Math.round(sidebar.getBoundingClientRect().width)
  document.documentElement.style.setProperty('--sidebar-width', `${width}px`)
}

function unlockSidebarWidth() {
  document.documentElement.style.removeProperty('--sidebar-width')
}

</script>

<template>
  <div class="app">
    <div class="resize-handle top" @mousedown.stop="startResize('top', $event)"></div>
    <div class="resize-handle bottom" @mousedown.stop="startResize('bottom', $event)"></div>
    <div class="resize-handle left" @mousedown.stop="startResize('left', $event)"></div>
    <div class="resize-handle right" @mousedown.stop="startResize('right', $event)"></div>
    <div class="resize-handle top-left" @mousedown.stop="startResize('top-left', $event)"></div>
    <div class="resize-handle top-right" @mousedown.stop="startResize('top-right', $event)"></div>
    <div class="resize-handle bottom-left" @mousedown.stop="startResize('bottom-left', $event)"></div>
    <div class="resize-handle bottom-right" @mousedown.stop="startResize('bottom-right', $event)"></div>

    <header
      class="app-titlebar"
      @dblclick="toggleMaximize"
      @mousedown.left="armWindowMove"
      @mousemove="maybeStartWindowMove"
      @mouseup.left="applyWindowSnap"
      @contextmenu.prevent="showSystemMenu"
    >
      <button
        class="app-icon"
        type="button"
        @mousedown.stop
        @dblclick.stop
        @click.stop="showSystemMenu"
      >
        <span class="app-icon-dot"></span>
      </button>
      <div class="app-title">ProtoFlow</div>
      <div class="title-actions">
        <button
          class="title-btn"
          type="button"
          @mousedown.stop
          @dblclick.stop
          @click.stop="minimizeWindow"
        >
          <span class="material-symbols-outlined">minimize</span>
        </button>
        <button
          class="title-btn"
          type="button"
          @mousedown.stop
          @dblclick.stop
          @click.stop="toggleMaximize"
        >
          <span class="material-symbols-outlined">crop_square</span>
        </button>
        <button
          class="title-btn close"
          type="button"
          @mousedown.stop
          @dblclick.stop
          @click.stop="closeWindow"
        >
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
    </header>

    <div class="app-shell">
      <aside ref="sidebarRef" class="sidebar">
        <div class="sidebar-header">
          <div class="brand-mark">
            <span class="material-symbols-outlined">hub</span>
          </div>
          <div>
          <div class="brand-name">ProtoFlow</div>
            <div class="brand-meta">{{ appVersionLabel }}</div>
          </div>
        </div>
        <nav class="sidebar-nav">
          <button class="nav-item" :class="{ active: currentView === 'manual' }" @click="currentView = 'manual'">
            <span class="material-symbols-outlined">terminal</span>
            <span>{{ uiLabels.manual }}</span>
          </button>
          <button class="nav-item" :class="{ active: currentView === 'scripts' }" @click="currentView = 'scripts'">
            <span class="material-symbols-outlined">smart_toy</span>
            <span>{{ uiLabels.scripts }}</span>
          </button>
          <button class="nav-item" :class="{ active: currentView === 'proxy' }" @click="currentView = 'proxy'">
            <span class="material-symbols-outlined">settings_input_hdmi</span>
            <span>{{ uiLabels.proxy }}</span>
          </button>
          <button class="nav-item" :class="{ active: currentView === 'protocols' }" @click="currentView = 'protocols'">
            <span class="material-symbols-outlined">cable</span>
            <span>{{ uiLabels.protocols }}</span>
          </button>
          <div class="nav-divider"></div>
          <button class="nav-item" :class="{ active: currentView === 'settings' }" @click="currentView = 'settings'">
            <span class="material-symbols-outlined">settings</span>
            <span>{{ uiLabels.settings }}</span>
          </button>
        </nav>
        <div class="sidebar-footer">
          <div class="user-avatar"></div>
          <div>
            <div class="user-name">DevUser_01</div>
            <div class="user-meta">{{ uiLabels.workspace }}</div>
          </div>
        </div>
      </aside>

      <main class="main">
        <ManualView v-if="currentView === 'manual'" />
        <ScriptsView v-else-if="currentView === 'scripts'" />
        <ProxyMonitorView
          v-else-if="currentView === 'proxy'"
          :capture-frames="captureFrames"
          :capture-meta="captureMeta"
          :capture-metrics="captureMetrics"
        />

        <section v-else-if="currentView === 'protocols'" class="page">
          <header class="page-header spaced">
            <div>
              <h2>{{ t('header.protocols.title') }}</h2>
              <p>{{ t('header.protocols.desc') }}</p>
            </div>
            <div class="header-actions">
              <button class="btn btn-outline" @click="refreshProtocols">
                <span class="material-symbols-outlined">refresh</span>
                {{ t('action.refresh') }}
              </button>
              <button class="btn btn-primary" @click="openCreateProtocol">
                <span class="material-symbols-outlined">add</span>
                {{ t('action.createProtocol') }}
              </button>
            </div>
          </header>
          <div class="tab-strip secondary">
            <button :class="{ active: protocolTab === 'all' }" @click="setProtocolTab('all')">{{ t('protocol.tab.all') }}</button>
            <button :class="{ active: protocolTab === 'modbus' }" @click="setProtocolTab('modbus')">Modbus</button>
            <button :class="{ active: protocolTab === 'tcp' }" @click="setProtocolTab('tcp')">TCP/IP</button>
            <button :class="{ active: protocolTab === 'custom' }" @click="setProtocolTab('custom')">{{ t('protocol.tab.custom') }}</button>
          </div>
          <div class="protocol-grid">
            <div v-for="card in filteredProtocolCards" :key="card.id" class="protocol-card">
              <div class="protocol-header">
                <div>
                  <div class="protocol-title">{{ card.name }}</div>
                  <div class="protocol-sub">{{ card.desc || tr('暂无描述') }}</div>
                </div>
                <span class="badge" :class="card.statusClass">{{ card.statusText }}</span>
              </div>
              <div class="protocol-rows">
                <div v-for="row in card.rows" :key="row.label" class="protocol-row">
                  <span>{{ row.label }}</span>
                  <strong>{{ row.value }}</strong>
                </div>
              </div>
              <div class="protocol-actions">
                <button class="btn btn-ghost" @click="openProtocolDetails(card)">
                  {{ card.source === 'custom' ? tr('配置') : tr('查看') }}
                </button>
                <button v-if="card.source === 'custom'" class="icon-btn" @click="openProtocolDelete(card)">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
            </div>
            <div v-if="filteredProtocolCards.length === 0" class="protocol-card empty">
              <div class="empty-icon">
                <span class="material-symbols-outlined">inventory_2</span>
              </div>
              <h3>{{ tr('暂无协议') }}</h3>
              <p>{{ tr('暂无可用协议，可从内置模板创建或新增自定义协议。') }}</p>
              <button class="btn btn-primary" @click="openCreateProtocol">
                <span class="material-symbols-outlined">add</span>
                {{ t('action.createProtocol') }}
              </button>
            </div>
          </div>
        </section>

<section v-else class="page">
          <header class="page-header spaced">
            <div>
              <h2>{{ t('header.settings.title') }}</h2>
                  <p>{{ t('header.settings.desc') }}</p>
            </div>
            <div class="header-actions">
              <button class="btn btn-outline" :disabled="!settingsDirty" @click="discardSettings">{{ t('action.discardChanges') }}</button>
              <button class="btn btn-primary" :disabled="!settingsDirty || settingsSaving" @click="saveSettings">
                <span class="material-symbols-outlined">save</span>{{ t('action.saveChanges') }}
              </button>
            </div>
            </header>
            <div class="tab-strip secondary">
              <button :class="{ active: settingsTab === 'general' }" @click="setSettingsTab('general')">{{ t('settings.tab.general') }}</button>
              <button :class="{ active: settingsTab === 'plugins' }" @click="setSettingsTab('plugins')">{{ t('settings.tab.plugins') }}</button>
              <button :class="{ active: settingsTab === 'runtime' }" @click="setSettingsTab('runtime')">{{ t('settings.tab.runtime') }}</button>
              <button :class="{ active: settingsTab === 'logs' }" @click="setSettingsTab('logs')">{{ t('settings.tab.logs') }}</button>
            </div>
            <div class="settings-stack">
              <div v-if="settingsTab === 'general'" class="panel" ref="settingsGeneralRef">
              <div class="panel-title simple">
                <span class="material-symbols-outlined">tune</span>{{ t('settings.tab.general') }}
              </div>
              <div class="form-grid">
                <label>
                  {{ t('settings.language') }}
                  <DropdownSelect
                    v-model="uiLanguage"
                    :options="languageOptions"
                  />
                </label>
                <label>
                  {{ t('settings.theme') }}
                  <DropdownSelect
                    v-model="uiTheme"
                    :options="themeOptions"
                  />
                </label>
              </div>
              <div class="toggle-row spaced">
                <div>
                  <strong>{{ t('settings.autoConnect.title') }}</strong>
                  <p>{{ t('settings.autoConnect.desc') }}</p>
                </div>
                <label class="switch">
                  <input v-model="autoConnectOnStart" type="checkbox" />
                  <span></span>
                </label>
              </div>
            </div>
              <div v-if="settingsTab === 'plugins'" class="panel" ref="settingsPluginsRef">
              <div class="panel-title simple">
                <span class="material-symbols-outlined">extension</span>{{ t('settings.tab.plugins') }}
              </div>
              <label class="file-row">
                {{ t('settings.workspace') }}
                <div class="file-input">
                  <span class="material-symbols-outlined">folder_open</span>
                  <input v-model="dslWorkspacePath" type="text" readonly />
                </div>
                <button class="btn btn-outline" type="button" @click="chooseDslWorkspace">{{ t('settings.chooseFolder') }}</button>
              </label>
              <div class="divider"></div>
              <div class="panel-title simple inline">
                {{ t('settings.plugins.title') }}
                <button class="link-btn">
                  <span class="material-symbols-outlined">refresh</span>
                  {{ t('settings.plugins.refresh') }}
                </button>
              </div>
              <div class="plugin-list">
                <div class="plugin-item">
                  <div>
                    <div class="plugin-title">Modbus TCP/RTU</div>
                    <div class="plugin-meta">{{ tr('v1.2.4 - 已启用') }}</div>
                  </div>
                  <span class="badge badge-green">{{ tr('已启用') }}</span>
                </div>
                <div class="plugin-item muted">
                  <div>
                    <div class="plugin-title">{{ tr('MQTT 适配器') }}</div>
                    <div class="plugin-meta">{{ tr('v0.9.8 - 未安装') }}</div>
                  </div>
                  <span class="badge badge-gray">{{ tr('未安装') }}</span>
                </div>
              </div>
              <div class="toggle-row spaced">
                <div>
                  <strong>{{ t('settings.autoConnect.title') }}</strong>
                  <p>{{ t('settings.autoConnect.desc') }}</p>
                </div>
                <label class="switch">
                  <input v-model="autoConnectOnStart" type="checkbox" />
                  <span></span>
                </label>
              </div>
            </div>

              <div v-if="settingsTab === 'runtime'" class="panel" ref="settingsRuntimeRef">
              <div class="panel-title simple">
                <span class="material-symbols-outlined">tune</span>{{ t('settings.tab.runtime') }}
              </div>
              <div class="empty-state muted">
                {{ tr('暂无可配置项，运行时设置将随着模块扩展开放。') }}
              </div>
            </div>

              <div v-if="settingsTab === 'logs'" class="panel" ref="settingsLogsRef">
              <div class="panel-title simple">
                <span class="material-symbols-outlined">folder_open</span>{{ t('settings.tab.logs') }}
              </div>
              <div class="empty-state muted">
                {{ tr('日志采集与归档策略将在后续版本中提供。') }}
              </div>
            </div>
          </div>
        </section>

        <div v-if="channelDialogOpen" class="modal-backdrop">
          <div class="channel-modal">
            <div class="modal-header">
              <div>
                <h3>{{ channelDialogMode === 'serial' ? tr('串口配置') : tr('新建通道') }}</h3>
                <p>{{ channelDialogMode === 'serial' ? tr('配置串口连接参数') : tr('配置新的通信连接参数') }}</p>
              </div>
              <button class="icon-btn" type="button" @click="closeChannelDialog">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
            <div class="modal-body">
              <div v-if="channelDialogMode !== 'serial'" class="channel-type-grid">
                <button
                  class="channel-type-card"
                  :class="{ active: channelType === 'serial' }"
                  type="button"
                  @click="channelType = 'serial'"
                >
                  <span class="material-symbols-outlined">settings_input_hdmi</span>
                  <span>{{ tr('串口 (Serial)') }}</span>
                </button>
                <button
                  class="channel-type-card"
                  :class="{ active: channelType === 'tcp' }"
                  type="button"
                  @click="channelType = 'tcp'"
                >
                  <span class="material-symbols-outlined">lan</span>
                  <span>{{ tr('TCP / 网络') }}</span>
                </button>
              </div>

              <div class="modal-section" v-if="channelDialogMode !== 'serial'">
                <div class="section-title">{{ tr('基本信息') }}</div>
                <div class="form-grid">
                  <label>{{ tr('通道名称') }}<input v-model="channelName" type="text" :placeholder="tr('例如：传感器A接口')" />
                  </label>
                  <label v-if="channelType === 'serial'">
                    {{ tr('串口端口') }}
                    <DropdownSelect
                      v-model="channelPort"
                      :options="portOptionsList"
                      :placeholder="ports.length ? tr('选择串口') : tr('无可用串口')"
                      :disabled="noPorts"
                      leading-icon="usb"
                    />
                  </label>
                  <label v-else>
                    {{ tr('目标地址') }}
                    <input v-model="channelHost" type="text" :placeholder="tr('例如：192.168.1.10')" />
                  </label>
                </div>
              </div>

              <div class="modal-section first" v-if="channelType === 'serial'">
                <div class="section-title">{{ tr('串口参数') }}</div>
                <div class="form-grid triple">
                  <label>
                    {{ tr('波特率') }}
                    <DropdownSelect v-model="channelBaud" :options="[9600, 19200, 38400, 57600, 115200]" />
                  </label>
                  <label>
                    {{ tr('数据位') }}
                    <DropdownSelect v-model="channelDataBits" :options="['7', '8']" />
                  </label>
                  <label>
                    {{ tr('停止位') }}
                    <DropdownSelect v-model="channelStopBits" :options="['1', '1.5', '2']" />
                  </label>
                </div>
                <div class="form-grid quad">
                  <label>
                    {{ tr('校验位') }}
                    <DropdownSelect
                      v-model="channelParity"
                      :options="[
                        { label: tr('无校验'), value: 'none' },
                        { label: tr('奇校验'), value: 'odd' },
                        { label: tr('偶校验'), value: 'even' },
                      ]"
                    />
                  </label>
                  <label>
                    {{ tr('流控') }}
                    <DropdownSelect
                      v-model="channelFlowControl"
                      :options="[
                        { label: tr('无'), value: 'none' },
                        { label: 'RTS/CTS', value: 'rtscts' },
                        { label: 'XON/XOFF', value: 'xonxoff' },
                      ]"
                    />
                  </label>
                  <label>
                    {{ tr('读超时 (ms)') }}
                    <input v-model.number="channelReadTimeout" type="number" min="0" placeholder="1000" />
                  </label>
                  <label>
                    {{ tr('写超时 (ms)') }}
                    <input v-model.number="channelWriteTimeout" type="number" min="0" placeholder="1000" />
                  </label>
                </div>
            </div>

              <div class="modal-section" v-else>
                <div class="form-grid">
                  <label>
                    {{ tr('TCP 端口') }}
                    <input v-model.number="channelTcpPort" type="number" />
                  </label>
                </div>
              </div>

              <label class="channel-toggle">
                <input v-model="channelAutoConnect" type="checkbox" />
                <span>{{ channelDialogMode === 'serial' ? tr('保存后立即连接') : tr('创建后立即启动连接') }}</span>
              </label>
            </div>
            <div class="modal-footer">
              <button class="btn btn-outline" type="button" @click="closeChannelDialog">{{ tr('取消') }}</button>
              <button class="btn btn-primary" type="button" @click="submitChannelDialog">
                {{ channelDialogMode === 'serial' ? tr('保存配置') : tr('创建通道') }}
              </button>
            </div>
          </div>
        </div>

      <teleport to="body">
        <div v-if="protocolDialogOpen" class="modal-backdrop" @mousedown.self="closeProtocolDialog">
          <div class="channel-modal protocol-modal" @mousedown.stop @click.stop>
            <div class="modal-header">
              <div>
                <h3>{{ protocolDialogMode === 'create' ? tr('新建协议') : protocolDialogMode === 'edit' ? tr('配置协议') : tr('协议详情') }}</h3>
                <p>{{ protocolDialogMode === 'create' ? tr('添加自定义协议元数据，供解析引擎识别。') : tr('查看或更新协议描述与分类。') }}</p>
              </div>
              <button class="icon-btn" type="button" @click="closeProtocolDialog">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
            <div class="modal-body protocol-modal-body">
              <div class="form-grid protocol-grid">
                <label>
                  {{ tr('协议名称') }}
                  <input v-model="protocolDraft.name" type="text" :disabled="protocolDialogMode === 'view'" />
                </label>
                <label>
                  {{ tr('键名') }}
                  <input v-model="protocolDraft.key" type="text" :disabled="protocolDialogMode !== 'create'" />
                </label>
              </div>
              <div class="form-grid protocol-grid">
                <label>
                  {{ tr('分类') }}
                  <select v-model="protocolDraft.category" :disabled="protocolDialogMode === 'view'">
                    <option value="modbus">Modbus</option>
                    <option value="tcp">TCP/IP</option>
                    <option value="custom">{{ t('protocol.tab.custom') }}</option>
                  </select>
                </label>
                <label>
                  {{ tr('状态') }}
                  <select v-model="protocolDraft.status" :disabled="protocolDialogMode === 'view'">
                    <option value="available">{{ tr('可用') }}</option>
                    <option value="custom">{{ t('protocol.tab.custom') }}</option>
                    <option value="disabled">{{ tr('已禁用') }}</option>
                  </select>
                </label>
              </div>
              <label class="protocol-textarea">
                {{ tr('描述') }}
                <textarea v-model="protocolDraft.desc" rows="3" :disabled="protocolDialogMode === 'view'"></textarea>
              </label>
              <div class="modal-section protocol-driver" v-if="protocolEditing && protocolEditing.driver">
                <div class="section-title">{{ tr('驱动') }}</div>
                <div class="form-grid protocol-grid">
                  <label>
                    {{ tr('驱动类') }}
                    <input :value="protocolEditing.driver" type="text" disabled />
                  </label>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-outline" type="button" @click="closeProtocolDialog">{{ tr('取消') }}</button>
              <button v-if="protocolDialogMode !== 'view'" class="btn btn-primary" type="button" @click="saveProtocol">{{ tr('保存') }}</button>
            </div>
          </div>
        </div>

        <div v-if="protocolDeleteOpen" class="modal-backdrop" @mousedown.self="closeProtocolDelete">
          <div class="quick-modal quick-modal-sm" @mousedown.stop @click.stop>
            <div class="modal-header">
              <div>
                <h3>{{ tr('删除协议') }}</h3>
                <p>{{ tr('确认删除自定义协议') }}“{{ protocolDeleting?.name }}”{{ tr('吗？') }}</p>
              </div>
              <button class="icon-btn" type="button" @click="closeProtocolDelete">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
            <div class="modal-footer">
              <button class="btn btn-outline" type="button" @click="closeProtocolDelete">{{ tr('取消') }}</button>
              <button class="btn btn-danger" type="button" @click="confirmProtocolDelete">{{ tr('确认删除') }}</button>
            </div>
          </div>
        </div>
      </teleport>

      <teleport to="body">
        <div v-if="uiModalOpen" class="modal-backdrop" @mousedown.self="closeUiYamlModal">
          <div class="channel-modal ui-yaml-modal" @mousedown.stop @click.stop>
            <div class="modal-header">
              <div>
                <h3>{{ tr('UI YAML 预览') }}</h3>
                <p>{{ tr('脚本运行中展示 UI 渲染结果') }}</p>
              </div>
              <button class="icon-btn" type="button" @click="closeUiYamlModal">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
            <div class="modal-body ui-yaml-body">
              <div v-if="uiRuntime.parseError" class="ui-yaml-error">
                <strong>{{ tr('解析失败') }}</strong>
                <div>{{ uiRuntime.parseError.message }}</div>
                <div v-if="uiRuntime.parseError.path" class="muted">Path: {{ uiRuntime.parseError.path }}</div>
                <div v-if="uiRuntime.parseError.line" class="muted">
                  Line {{ uiRuntime.parseError.line }}, Column {{ uiRuntime.parseError.column || 0 }}
                </div>
              </div>
              <div v-else-if="uiRuntime.lastGoodConfig">
                <LayoutRenderer :config="uiRuntime.lastGoodConfig" :widgetsById="uiRuntime.widgetsById" />
              </div>
              <div v-else class="empty-state muted">{{ tr('暂无可渲染的 UI 配置') }}</div>
            </div>
          </div>
        </div>
      </teleport>

</main>
    </div>

    <div v-if="snapPreview" class="snap-overlay" :class="`snap-${snapPreview}`"></div>
  </div>
</template>


