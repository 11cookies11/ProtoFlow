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
  'MQTT 适配器': 'MQTT 適配器',
  'TCP / 网络': 'TCP / 網路',
  'TCP 客户端': 'TCP 用戶端',
  'TCP 服务端': 'TCP 伺服端',
  'TCP 端口': 'TCP 連接埠',
  'UI YAML 预览': 'UI YAML 預覽',
  'v0.9.8 - 未安装': 'v0.9.8 - 未安裝',
  'v1.2.4 - 已启用': 'v1.2.4 - 已啟用',
  '串口 (Serial)': '串口 (Serial)',
  '串口参数': '串口參數',
  '串口端口': '串口埠',
  '串口通道': '串口通道',
  '串口配置': '串口設定',
  '例如：192.168.1.10': '例如：192.168.1.10',
  '例如：传感器A接口': '例如：感測器A介面',
  '保存': '儲存',
  '保存后立即连接': '儲存後立即連線',
  '保存配置': '儲存設定',
  '停止位': '停止位',
  '偶校验': '偶校驗',
  '写超时 (ms)': '寫入逾時 (ms)',
  '分类': '分類',
  '创建后立即启动连接': '建立後立即啟動連線',
  '创建通道': '建立通道',
  '删除协议': '刪除協定',
  '协议': '協定',
  '协议名称': '協定名稱',
  '协议详情': '協定詳情',
  '取消': '取消',
  '可用': '可用',
  '吗？': '嗎？',
  '基本信息': '基本資訊',
  '奇校验': '奇校驗',
  '已启用': '已啟用',
  '已禁用': '已停用',
  '描述': '描述',
  '搜索关键词': '搜尋關鍵字',
  '数据位': '資料位',
  '新建协议': '新增協定',
  '新建通道': '新增通道',
  '无': '無',
  '无可用串口': '無可用串口',
  '无校验': '無校驗',
  '日志采集与归档策略将在后续版本中提供。': '日誌採集與歸檔策略將在後續版本中提供。',
  '暂无协议': '暫無協定',
  '暂无可渲染的 UI 配置': '暫無可渲染的 UI 設定',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': '暫無可用協定，可從內建範本建立或新增自訂協定。',
  '暂无可配置项，运行时设置将随着模块扩展开放。': '暫無可設定項，執行時設定將隨模組擴充開放。',
  '暂无描述': '暫無描述',
  '未安装': '未安裝',
  '未知': '未知',
  '查看': '檢視',
  '查看或更新协议描述与分类。': '檢視或更新協定描述與分類。',
  '校验位': '校驗位',
  '波特率': '波特率',
  '流控': '流控',
  '添加自定义协议元数据，供解析引擎识别。': '新增自訂協定中繼資料，供解析引擎識別。',
  '状态': '狀態',
  '目标地址': '目標位址',
  '确认删除': '確認刪除',
  '确认删除自定义协议': '確認刪除自訂協定',
  '空闲': '閒置',
  '端口': '埠',
  '脚本运行中展示 UI 渲染结果': '腳本執行中顯示 UI 渲染結果',
  '自定义': '自訂',
  '解析失败': '解析失敗',
  '请输入指令名称和内容': '請輸入指令名稱與內容',
  '读超时 (ms)': '讀取逾時 (ms)',
  '运行中': '執行中',
  '选择串口': '選擇串口',
  '选择工作区': '選擇工作區',
  '通道名称': '通道名稱',
  '配置': '設定',
  '配置串口连接参数': '設定串口連線參數',
  '配置协议': '設定協定',
  '配置新的通信连接参数': '設定新的通訊連線參數',
  '键名': '鍵名',
  '驱动': '驅動',
  '驱动类': '驅動類別',
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
  'MQTT 适配器': 'MQTT アダプター',
  'TCP / 网络': 'TCP / ネットワーク',
  'TCP 客户端': 'TCP クライアント',
  'TCP 服务端': 'TCP サーバー',
  'TCP 端口': 'TCP ポート',
  'UI YAML 预览': 'UI YAML プレビュー',
  'v0.9.8 - 未安装': 'v0.9.8 - 未インストール',
  'v1.2.4 - 已启用': 'v1.2.4 - 有効',
  '串口 (Serial)': 'シリアル (Serial)',
  '串口参数': 'シリアルパラメータ',
  '串口端口': 'シリアルポート',
  '串口通道': 'シリアルチャネル',
  '串口配置': 'シリアル設定',
  '例如：192.168.1.10': '例：192.168.1.10',
  '例如：传感器A接口': '例：センサーAインターフェース',
  '保存': '保存',
  '保存后立即连接': '保存後すぐに接続',
  '保存配置': '設定を保存',
  '停止位': 'ストップビット',
  '偶校验': '偶数パリティ',
  '写超时 (ms)': '書き込みタイムアウト (ms)',
  '分类': '分類',
  '创建后立即启动连接': '作成後すぐに接続を開始',
  '创建通道': 'チャネルを作成',
  '删除协议': 'プロトコルを削除',
  '协议': 'プロトコル',
  '协议名称': 'プロトコル名',
  '协议详情': 'プロトコル詳細',
  '取消': 'キャンセル',
  '可用': '利用可能',
  '吗？': '？',
  '基本信息': '基本情報',
  '奇校验': '奇数パリティ',
  '已启用': '有効',
  '已禁用': '無効',
  '描述': '説明',
  '搜索关键词': '検索キーワード',
  '数据位': 'データビット',
  '新建协议': '新規プロトコル',
  '新建通道': '新規チャネル',
  '无': 'なし',
  '无可用串口': '利用可能なシリアルポートがありません',
  '无校验': 'パリティなし',
  '日志采集与归档策略将在后续版本中提供。': 'ログ収集とアーカイブ方針は後続バージョンで提供予定です。',
  '暂无协议': 'プロトコルがありません',
  '暂无可渲染的 UI 配置': 'レンダリング可能な UI 設定がありません',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': '利用可能なプロトコルがありません。内蔵テンプレートから作成するか、カスタムを追加してください。',
  '暂无可配置项，运行时设置将随着模块扩展开放。': '設定可能な項目がありません。実行時設定はモジュール拡張に合わせて公開されます。',
  '暂无描述': '説明なし',
  '未安装': '未インストール',
  '未知': '不明',
  '查看': '表示',
  '查看或更新协议描述与分类。': 'プロトコルの説明と分類を表示または更新します。',
  '校验位': 'パリティ',
  '波特率': 'ボーレート',
  '流控': 'フロー制御',
  '添加自定义协议元数据，供解析引擎识别。': '解析エンジンが識別できるようにカスタムプロトコルのメタデータを追加します。',
  '状态': '状態',
  '目标地址': '宛先アドレス',
  '确认删除': '削除を確認',
  '确认删除自定义协议': 'カスタムプロトコルの削除を確認',
  '空闲': 'アイドル',
  '端口': 'ポート',
  '脚本运行中展示 UI 渲染结果': 'スクリプト実行中に UI レンダリング結果を表示',
  '自定义': 'カスタム',
  '解析失败': '解析失敗',
  '请输入指令名称和内容': 'コマンド名と内容を入力してください',
  '读超时 (ms)': '読み取りタイムアウト (ms)',
  '运行中': '実行中',
  '选择串口': 'シリアルポートを選択',
  '选择工作区': 'ワークスペースを選択',
  '通道名称': 'チャネル名',
  '配置': '設定',
  '配置串口连接参数': 'シリアル接続パラメータを設定',
  '配置协议': 'プロトコルを設定',
  '配置新的通信连接参数': '新しい通信接続パラメータを設定',
  '键名': 'キー名',
  '驱动': 'ドライバー',
  '驱动类': 'ドライバークラス',
}
const koKR = {
  ...enUS,
  'nav.manual': '시리얼 터미널',
  'nav.scripts': '자동화 스크립트',
  'nav.proxy': '프록시 모니터',
  'nav.protocols': '프로토콜 관리자',
  'nav.settings': '설정',
  'nav.workspace': '관리자 작업공간',
  'status.connected': '연결됨',
  'status.connecting': '연결 중',
  'status.error': '오류',
  'status.disconnected': '연결 끊김',
  'theme.system': '시스템',
  'theme.dark': '다크(엔지니어)',
  'theme.light': '라이트',
  'header.protocols.title': '프로토콜 관리자',
  'header.protocols.desc': '프로토콜을 정의하고 채널을 바인딩하며 파싱 규칙을 구성합니다.',
  'action.refresh': '새로고침',
  'action.createProtocol': '새 프로토콜',
  'protocol.tab.all': '모든 프로토콜',
  'protocol.tab.custom': '사용자 정의',
  'header.settings.title': '앱 설정',
  'header.settings.desc': '전역 환경설정, 기본값 및 런타임 구성을 관리합니다.',
  'action.discardChanges': '변경 사항 취소',
  'action.saveChanges': '변경 사항 저장',
  'settings.tab.general': '일반',
  'settings.tab.plugins': '플러그인',
  'settings.tab.runtime': '런타임',
  'settings.tab.logs': '로그',
  'settings.language': '언어',
  'settings.theme': '테마',
  'settings.autoConnect.title': '시작 시 자동 연결',
  'settings.autoConnect.desc': '마지막 활성 채널에 자동으로 다시 연결합니다.',
  'settings.workspace': '작업공간',
  'settings.chooseFolder': '폴더 선택',
  'settings.plugins.title': '플러그인',
  'settings.plugins.refresh': '목록 새로고침',
  '空闲': '유휴',
  '串口通道': '시리얼 채널',
  'TCP 客户端': 'TCP 클라이언트',
  'TCP 服务端': 'TCP 서버',
  '端口': '포트',
  '运行中': '실행 중',
  '请输入指令名称和内容': '명령 이름과 내용을 입력하세요',
  '协议': '프로토콜',
  '可用': '사용 가능',
  '自定义': '사용자 정의',
  '已禁用': '비활성화',
  '未知': '알 수 없음',
  '键名': '키',
  '驱动': '드라이버',
  '分类': '카테고리',
  '搜索关键词': '키워드 검색',
  '选择工作区': '작업공간 선택',
  '暂无描述': '설명 없음',
  '配置': '구성',
  '查看': '보기',
  '暂无协议': '프로토콜 없음',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': '사용 가능한 프로토콜이 없습니다. 내장 템플릿에서 만들거나 사용자 정의를 추가하세요.',
  'v1.2.4 - 已启用': 'v1.2.4 - 사용',
  '已启用': '활성화',
  'MQTT 适配器': 'MQTT 어댑터',
  'v0.9.8 - 未安装': 'v0.9.8 - 미설치',
  '未安装': '미설치',
  '暂无可配置项，运行时设置将随着模块扩展开放。': '구성할 항목이 없습니다. 런타임 설정은 모듈 확장에 따라 제공됩니다.',
  '日志采集与归档策略将在后续版本中提供。': '로그 수집 및 아카이브 정책은 이후 버전에서 제공됩니다.',
  '串口配置': '시리얼 구성',
  '新建通道': '새 채널',
  '配置串口连接参数': '시리얼 연결 파라미터 구성',
  '配置新的通信连接参数': '새 통신 연결 파라미터 구성',
  '串口 (Serial)': '시리얼 (Serial)',
  'TCP / 网络': 'TCP / 네트워크',
  '基本信息': '기본 정보',
  '通道名称': '채널 이름',
  '例如：传感器A接口': '예: 센서 A 인터페이스',
  '串口端口': '시리얼 포트',
  '选择串口': '시리얼 포트 선택',
  '无可用串口': '사용 가능한 시리얼 포트 없음',
  '目标地址': '대상 주소',
  '例如：192.168.1.10': '예: 192.168.1.10',
  '串口参数': '시리얼 파라미터',
  '波特率': '보드레이트',
  '数据位': '데이터 비트',
  '停止位': '정지 비트',
  '校验位': '패리티',
  '无校验': '패리티 없음',
  '奇校验': '홀수 패리티',
  '偶校验': '짝수 패리티',
  '流控': '흐름 제어',
  '无': '없음',
  '读超时 (ms)': '읽기 타임아웃 (ms)',
  '写超时 (ms)': '쓰기 타임아웃 (ms)',
  'TCP 端口': 'TCP 포트',
  '保存后立即连接': '저장 후 즉시 연결',
  '创建后立即启动连接': '생성 후 즉시 연결 시작',
  '取消': '취소',
  '保存配置': '구성 저장',
  '创建通道': '채널 생성',
  '新建协议': '새 프로토콜',
  '配置协议': '프로토콜 구성',
  '协议详情': '프로토콜 상세',
  '添加自定义协议元数据，供解析引擎识别。': '파서 엔진이 인식하도록 사용자 정의 프로토콜 메타데이터를 추가합니다.',
  '查看或更新协议描述与分类。': '프로토콜 설명과 분류를 보기 또는 업데이트합니다.',
  '协议名称': '프로토콜 이름',
  '状态': '상태',
  '描述': '설명',
  '驱动类': '드라이버 클래스',
  '保存': '저장',
  '删除协议': '프로토콜 삭제',
  '确认删除自定义协议': '사용자 정의 프로토콜 삭제 확인',
  '吗？': '?',
  '确认删除': '삭제 확인',
  'UI YAML 预览': 'UI YAML 미리보기',
  '脚本运行中展示 UI 渲染结果': '스크립트 실행 중 UI 렌더링 결과 표시',
  '解析失败': '파싱 실패',
  '暂无可渲染的 UI 配置': '렌더링 가능한 UI 설정 없음',
}
const frFR = {
  ...enUS,
  'nav.manual': 'Terminal série',
  'nav.scripts': 'Scripts d’automatisation',
  'nav.proxy': 'Surveillance proxy',
  'nav.protocols': 'Gestionnaire de protocoles',
  'nav.settings': 'Paramètres',
  'nav.workspace': 'Espace de travail admin',
  'status.connected': 'Connecté',
  'status.connecting': 'Connexion',
  'status.error': 'Erreur',
  'status.disconnected': 'Déconnecté',
  'theme.system': 'Système',
  'theme.dark': 'Sombre (Ingénieur)',
  'theme.light': 'Clair',
  'header.protocols.title': 'Gestionnaire de protocoles',
  'header.protocols.desc': 'Définissez les protocoles, associez les canaux et configurez les règles d’analyse.',
  'action.refresh': 'Actualiser',
  'action.createProtocol': 'Nouveau protocole',
  'protocol.tab.all': 'Tous les protocoles',
  'protocol.tab.custom': 'Personnalisé',
  'header.settings.title': 'Paramètres de l’application',
  'header.settings.desc': 'Gérez les préférences globales, les valeurs par défaut et la configuration d’exécution.',
  'action.discardChanges': 'Ignorer les modifications',
  'action.saveChanges': 'Enregistrer les modifications',
  'settings.tab.general': 'Général',
  'settings.tab.plugins': 'Plugins',
  'settings.tab.runtime': 'Exécution',
  'settings.tab.logs': 'Journaux',
  'settings.language': 'Langue',
  'settings.theme': 'Thème',
  'settings.autoConnect.title': 'Connexion automatique au démarrage',
  'settings.autoConnect.desc': 'Reconnecter automatiquement le dernier canal actif.',
  'settings.workspace': 'Espace de travail',
  'settings.chooseFolder': 'Choisir un dossier',
  'settings.plugins.title': 'Plugins',
  'settings.plugins.refresh': 'Actualiser la liste',
  '空闲': 'Inactif',
  '串口通道': 'Canal série',
  'TCP 客户端': 'Client TCP',
  'TCP 服务端': 'Serveur TCP',
  '端口': 'Port',
  '运行中': 'En cours',
  '请输入指令名称和内容': 'Saisissez le nom et le contenu de la commande',
  '协议': 'Protocole',
  '可用': 'Disponible',
  '自定义': 'Personnalisé',
  '已禁用': 'Désactivé',
  '未知': 'Inconnu',
  '键名': 'Clé',
  '驱动': 'Pilote',
  '分类': 'Catégorie',
  '搜索关键词': 'Rechercher des mots-clés',
  '选择工作区': 'Sélectionner l’espace de travail',
  '暂无描述': 'Aucune description',
  '配置': 'Configurer',
  '查看': 'Voir',
  '暂无协议': 'Aucun protocole',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Aucun protocole disponible. Créez-en depuis les modèles intégrés ou ajoutez un personnalisé.',
  'v1.2.4 - 已启用': 'v1.2.4 - Activé',
  '已启用': 'Activé',
  'MQTT 适配器': 'Adaptateur MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - Non installé',
  '未安装': 'Non installé',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Aucun élément configurable. Les paramètres d’exécution seront disponibles à mesure que les modules s’étendent.',
  '日志采集与归档策略将在后续版本中提供。': 'Les politiques de collecte et d’archivage des journaux seront disponibles dans une version ultérieure.',
  '串口配置': 'Configuration série',
  '新建通道': 'Nouveau canal',
  '配置串口连接参数': 'Configurer les paramètres de connexion série',
  '配置新的通信连接参数': 'Configurer de nouveaux paramètres de connexion',
  '串口 (Serial)': 'Série (Serial)',
  'TCP / 网络': 'TCP / Réseau',
  '基本信息': 'Infos de base',
  '通道名称': 'Nom du canal',
  '例如：传感器A接口': 'Exemple : interface du capteur A',
  '串口端口': 'Port série',
  '选择串口': 'Sélectionner le port série',
  '无可用串口': 'Aucun port série disponible',
  '目标地址': 'Adresse cible',
  '例如：192.168.1.10': 'Exemple : 192.168.1.10',
  '串口参数': 'Paramètres série',
  '波特率': 'Débit en bauds',
  '数据位': 'Bits de données',
  '停止位': 'Bits d’arrêt',
  '校验位': 'Parité',
  '无校验': 'Aucune parité',
  '奇校验': 'Parité impaire',
  '偶校验': 'Parité paire',
  '流控': 'Contrôle de flux',
  '无': 'Aucun',
  '读超时 (ms)': 'Délai de lecture (ms)',
  '写超时 (ms)': 'Délai d’écriture (ms)',
  'TCP 端口': 'Port TCP',
  '保存后立即连接': 'Connecter après l’enregistrement',
  '创建后立即启动连接': 'Démarrer la connexion après la création',
  '取消': 'Annuler',
  '保存配置': 'Enregistrer la configuration',
  '创建通道': 'Créer un canal',
  '新建协议': 'Nouveau protocole',
  '配置协议': 'Configurer le protocole',
  '协议详情': 'Détails du protocole',
  '添加自定义协议元数据，供解析引擎识别。': 'Ajouter des métadonnées de protocole personnalisées pour que le moteur d’analyse les reconnaisse.',
  '查看或更新协议描述与分类。': 'Afficher ou mettre à jour la description et la catégorie du protocole.',
  '协议名称': 'Nom du protocole',
  '状态': 'Statut',
  '描述': 'Description',
  '驱动类': 'Classe de pilote',
  '保存': 'Enregistrer',
  '删除协议': 'Supprimer le protocole',
  '确认删除自定义协议': 'Confirmer la suppression du protocole personnalisé',
  '吗？': '?',
  '确认删除': 'Confirmer la suppression',
  'UI YAML 预览': 'Aperçu UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Afficher le rendu UI pendant l’exécution du script',
  '解析失败': 'Échec de l’analyse',
  '暂无可渲染的 UI 配置': 'Aucune configuration UI rendable',
}
const deDE = {
  ...enUS,
  'nav.manual': 'Serielles Terminal',
  'nav.scripts': 'Automationsskripte',
  'nav.proxy': 'Proxy-Monitor',
  'nav.protocols': 'Protokoll-Manager',
  'nav.settings': 'Einstellungen',
  'nav.workspace': 'Admin-Arbeitsbereich',
  'status.connected': 'Verbunden',
  'status.connecting': 'Verbindung wird hergestellt',
  'status.error': 'Fehler',
  'status.disconnected': 'Getrennt',
  'theme.system': 'System',
  'theme.dark': 'Dunkel (Ingenieur)',
  'theme.light': 'Hell',
  'header.protocols.title': 'Protokoll-Manager',
  'header.protocols.desc': 'Protokolle definieren, Kanäle binden und Parsing-Regeln konfigurieren.',
  'action.refresh': 'Aktualisieren',
  'action.createProtocol': 'Neues Protokoll',
  'protocol.tab.all': 'Alle Protokolle',
  'protocol.tab.custom': 'Benutzerdefiniert',
  'header.settings.title': 'App-Einstellungen',
  'header.settings.desc': 'Globale Einstellungen, Standardwerte und Laufzeitkonfiguration verwalten.',
  'action.discardChanges': 'Änderungen verwerfen',
  'action.saveChanges': 'Änderungen speichern',
  'settings.tab.general': 'Allgemein',
  'settings.tab.plugins': 'Plugins',
  'settings.tab.runtime': 'Laufzeit',
  'settings.tab.logs': 'Protokolle',
  'settings.language': 'Sprache',
  'settings.theme': 'Design',
  'settings.autoConnect.title': 'Beim Start automatisch verbinden',
  'settings.autoConnect.desc': 'Automatisch mit dem zuletzt aktiven Kanal verbinden.',
  'settings.workspace': 'Arbeitsbereich',
  'settings.chooseFolder': 'Ordner auswählen',
  'settings.plugins.title': 'Plugins',
  'settings.plugins.refresh': 'Liste aktualisieren',
  '空闲': 'Leerlauf',
  '串口通道': 'Serieller Kanal',
  'TCP 客户端': 'TCP-Client',
  'TCP 服务端': 'TCP-Server',
  '端口': 'Port',
  '运行中': 'Läuft',
  '请输入指令名称和内容': 'Befehlname und Inhalt eingeben',
  '协议': 'Protokoll',
  '可用': 'Verfügbar',
  '自定义': 'Benutzerdefiniert',
  '已禁用': 'Deaktiviert',
  '未知': 'Unbekannt',
  '键名': 'Schlüssel',
  '驱动': 'Treiber',
  '分类': 'Kategorie',
  '搜索关键词': 'Schlüsselwörter suchen',
  '选择工作区': 'Arbeitsbereich auswählen',
  '暂无描述': 'Keine Beschreibung',
  '配置': 'Konfigurieren',
  '查看': 'Anzeigen',
  '暂无协议': 'Keine Protokolle',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Keine Protokolle verfügbar. Aus integrierten Vorlagen erstellen oder benutzerdefiniert hinzufügen.',
  'v1.2.4 - 已启用': 'v1.2.4 - Aktiviert',
  '已启用': 'Aktiviert',
  'MQTT 适配器': 'MQTT-Adapter',
  'v0.9.8 - 未安装': 'v0.9.8 - Nicht installiert',
  '未安装': 'Nicht installiert',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Keine konfigurierbaren Elemente. Laufzeiteinstellungen werden mit Modulerweiterungen verfügbar.',
  '日志采集与归档策略将在后续版本中提供。': 'Richtlinien zur Protokollerfassung und Archivierung werden in einer zukünftigen Version verfügbar sein.',
  '串口配置': 'Serielle Konfiguration',
  '新建通道': 'Neuer Kanal',
  '配置串口连接参数': 'Serielle Verbindungsparameter konfigurieren',
  '配置新的通信连接参数': 'Neue Verbindungsparameter konfigurieren',
  '串口 (Serial)': 'Seriell (Serial)',
  'TCP / 网络': 'TCP / Netzwerk',
  '基本信息': 'Grundinformationen',
  '通道名称': 'Kanalname',
  '例如：传感器A接口': 'Beispiel: Sensor-A-Schnittstelle',
  '串口端口': 'Serieller Port',
  '选择串口': 'Seriellen Port auswählen',
  '无可用串口': 'Keine seriellen Ports verfügbar',
  '目标地址': 'Zieladresse',
  '例如：192.168.1.10': 'Beispiel: 192.168.1.10',
  '串口参数': 'Serielle Parameter',
  '波特率': 'Baudrate',
  '数据位': 'Datenbits',
  '停止位': 'Stoppbits',
  '校验位': 'Parität',
  '无校验': 'Keine Parität',
  '奇校验': 'Ungerade Parität',
  '偶校验': 'Gerade Parität',
  '流控': 'Flusskontrolle',
  '无': 'Keine',
  '读超时 (ms)': 'Lese-Timeout (ms)',
  '写超时 (ms)': 'Schreib-Timeout (ms)',
  'TCP 端口': 'TCP-Port',
  '保存后立即连接': 'Nach dem Speichern verbinden',
  '创建后立即启动连接': 'Verbindung nach Erstellung starten',
  '取消': 'Abbrechen',
  '保存配置': 'Konfiguration speichern',
  '创建通道': 'Kanal erstellen',
  '新建协议': 'Neues Protokoll',
  '配置协议': 'Protokoll konfigurieren',
  '协议详情': 'Protokolldetails',
  '添加自定义协议元数据，供解析引擎识别。': 'Benutzerdefinierte Protokoll-Metadaten hinzufügen, damit die Engine sie erkennt.',
  '查看或更新协议描述与分类。': 'Protokollbeschreibung und Kategorie anzeigen oder aktualisieren.',
  '协议名称': 'Protokollname',
  '状态': 'Status',
  '描述': 'Beschreibung',
  '驱动类': 'Treiberklasse',
  '保存': 'Speichern',
  '删除协议': 'Protokoll löschen',
  '确认删除自定义协议': 'Benutzerdefiniertes Protokoll löschen bestätigen',
  '吗？': '?',
  '确认删除': 'Löschen bestätigen',
  'UI YAML 预览': 'UI-YAML-Vorschau',
  '脚本运行中展示 UI 渲染结果': 'UI-Rendering während der Skriptausführung anzeigen',
  '解析失败': 'Parsing fehlgeschlagen',
  '暂无可渲染的 UI 配置': 'Keine renderbare UI-Konfiguration',
}
const esES = {
  ...enUS,
  'nav.manual': 'Terminal serie',
  'nav.scripts': 'Scripts de automatización',
  'nav.proxy': 'Monitor de proxy',
  'nav.protocols': 'Gestor de protocolos',
  'nav.settings': 'Ajustes',
  'nav.workspace': 'Espacio de trabajo admin',
  'status.connected': 'Conectado',
  'status.connecting': 'Conectando',
  'status.error': 'Error',
  'status.disconnected': 'Desconectado',
  'theme.system': 'Sistema',
  'theme.dark': 'Oscuro (Ingeniero)',
  'theme.light': 'Claro',
  'header.protocols.title': 'Gestor de protocolos',
  'header.protocols.desc': 'Defina protocolos, vincule canales y configure reglas de análisis.',
  'action.refresh': 'Actualizar',
  'action.createProtocol': 'Nuevo protocolo',
  'protocol.tab.all': 'Todos los protocolos',
  'protocol.tab.custom': 'Personalizado',
  'header.settings.title': 'Ajustes de la aplicación',
  'header.settings.desc': 'Gestione preferencias globales, valores predeterminados y la configuración de ejecución.',
  'action.discardChanges': 'Descartar cambios',
  'action.saveChanges': 'Guardar cambios',
  'settings.tab.general': 'General',
  'settings.tab.plugins': 'Plugins',
  'settings.tab.runtime': 'Tiempo de ejecución',
  'settings.tab.logs': 'Registros',
  'settings.language': 'Idioma',
  'settings.theme': 'Tema',
  'settings.autoConnect.title': 'Conexión automática al iniciar',
  'settings.autoConnect.desc': 'Reconectar automáticamente al último canal activo.',
  'settings.workspace': 'Espacio de trabajo',
  'settings.chooseFolder': 'Elegir carpeta',
  'settings.plugins.title': 'Plugins',
  'settings.plugins.refresh': 'Actualizar lista',
  '空闲': 'Inactivo',
  '串口通道': 'Canal serie',
  'TCP 客户端': 'Cliente TCP',
  'TCP 服务端': 'Servidor TCP',
  '端口': 'Puerto',
  '运行中': 'En ejecución',
  '请输入指令名称和内容': 'Introduzca el nombre y el contenido del comando',
  '协议': 'Protocolo',
  '可用': 'Disponible',
  '自定义': 'Personalizado',
  '已禁用': 'Deshabilitado',
  '未知': 'Desconocido',
  '键名': 'Clave',
  '驱动': 'Controlador',
  '分类': 'Categoría',
  '搜索关键词': 'Buscar palabras clave',
  '选择工作区': 'Seleccionar espacio de trabajo',
  '暂无描述': 'Sin descripción',
  '配置': 'Configurar',
  '查看': 'Ver',
  '暂无协议': 'Sin protocolos',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'No hay protocolos disponibles. Cree desde plantillas integradas o añada uno personalizado.',
  'v1.2.4 - 已启用': 'v1.2.4 - Habilitado',
  '已启用': 'Habilitado',
  'MQTT 适配器': 'Adaptador MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - No instalado',
  '未安装': 'No instalado',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'No hay elementos configurables. Los ajustes de ejecución se abrirán a medida que se amplíen los módulos.',
  '日志采集与归档策略将在后续版本中提供。': 'Las políticas de recopilación y archivado de registros estarán disponibles en una versión futura.',
  '串口配置': 'Configuración serie',
  '新建通道': 'Nuevo canal',
  '配置串口连接参数': 'Configurar parámetros de conexión serie',
  '配置新的通信连接参数': 'Configurar nuevos parámetros de conexión',
  '串口 (Serial)': 'Serie (Serial)',
  'TCP / 网络': 'TCP / Red',
  '基本信息': 'Información básica',
  '通道名称': 'Nombre del canal',
  '例如：传感器A接口': 'Ejemplo: interfaz del sensor A',
  '串口端口': 'Puerto serie',
  '选择串口': 'Seleccionar puerto serie',
  '无可用串口': 'No hay puertos serie disponibles',
  '目标地址': 'Dirección de destino',
  '例如：192.168.1.10': 'Ejemplo: 192.168.1.10',
  '串口参数': 'Parámetros serie',
  '波特率': 'Velocidad en baudios',
  '数据位': 'Bits de datos',
  '停止位': 'Bits de parada',
  '校验位': 'Paridad',
  '无校验': 'Sin paridad',
  '奇校验': 'Paridad impar',
  '偶校验': 'Paridad par',
  '流控': 'Control de flujo',
  '无': 'Ninguno',
  '读超时 (ms)': 'Tiempo de espera de lectura (ms)',
  '写超时 (ms)': 'Tiempo de espera de escritura (ms)',
  'TCP 端口': 'Puerto TCP',
  '保存后立即连接': 'Conectar después de guardar',
  '创建后立即启动连接': 'Iniciar conexión después de la creación',
  '取消': 'Cancelar',
  '保存配置': 'Guardar configuración',
  '创建通道': 'Crear canal',
  '新建协议': 'Nuevo protocolo',
  '配置协议': 'Configurar protocolo',
  '协议详情': 'Detalles del protocolo',
  '添加自定义协议元数据，供解析引擎识别。': 'Añadir metadatos de protocolo personalizados para que el motor los reconozca.',
  '查看或更新协议描述与分类。': 'Ver o actualizar la descripción y la categoría del protocolo.',
  '协议名称': 'Nombre del protocolo',
  '状态': 'Estado',
  '描述': 'Descripción',
  '驱动类': 'Clase de controlador',
  '保存': 'Guardar',
  '删除协议': 'Eliminar protocolo',
  '确认删除自定义协议': 'Confirmar eliminación del protocolo personalizado',
  '吗？': '?',
  '确认删除': 'Confirmar eliminación',
  'UI YAML 预览': 'Vista previa de UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Mostrar renderizado de UI mientras se ejecuta el script',
  '解析失败': 'Error de análisis',
  '暂无可渲染的 UI 配置': 'No hay configuración de UI renderizable',
}
const ptBR = {
  ...enUS,
  'nav.manual': 'Terminal serial',
  'nav.scripts': 'Scripts de automação',
  'nav.proxy': 'Monitor de proxy',
  'nav.protocols': 'Gerenciador de protocolos',
  'nav.settings': 'Configurações',
  'nav.workspace': 'Espaço de trabalho admin',
  'status.connected': 'Conectado',
  'status.connecting': 'Conectando',
  'status.error': 'Erro',
  'status.disconnected': 'Desconectado',
  'theme.system': 'Sistema',
  'theme.dark': 'Escuro (Engenheiro)',
  'theme.light': 'Claro',
  'header.protocols.title': 'Gerenciador de protocolos',
  'header.protocols.desc': 'Defina protocolos, vincule canais e configure regras de parsing.',
  'action.refresh': 'Atualizar',
  'action.createProtocol': 'Novo protocolo',
  'protocol.tab.all': 'Todos os protocolos',
  'protocol.tab.custom': 'Personalizado',
  'header.settings.title': 'Configurações do app',
  'header.settings.desc': 'Gerencie preferências globais, padrões e configuração de execução.',
  'action.discardChanges': 'Descartar alterações',
  'action.saveChanges': 'Salvar alterações',
  'settings.tab.general': 'Geral',
  'settings.tab.plugins': 'Plugins',
  'settings.tab.runtime': 'Tempo de execução',
  'settings.tab.logs': 'Logs',
  'settings.language': 'Idioma',
  'settings.theme': 'Tema',
  'settings.autoConnect.title': 'Conectar automaticamente ao iniciar',
  'settings.autoConnect.desc': 'Reconectar automaticamente ao último canal ativo.',
  'settings.workspace': 'Espaço de trabalho',
  'settings.chooseFolder': 'Escolher pasta',
  'settings.plugins.title': 'Plugins',
  'settings.plugins.refresh': 'Atualizar lista',
  '空闲': 'Inativo',
  '串口通道': 'Canal serial',
  'TCP 客户端': 'Cliente TCP',
  'TCP 服务端': 'Servidor TCP',
  '端口': 'Porta',
  '运行中': 'Em execução',
  '请输入指令名称和内容': 'Digite o nome e o conteúdo do comando',
  '协议': 'Protocolo',
  '可用': 'Disponível',
  '自定义': 'Personalizado',
  '已禁用': 'Desativado',
  '未知': 'Desconhecido',
  '键名': 'Chave',
  '驱动': 'Driver',
  '分类': 'Categoria',
  '搜索关键词': 'Buscar palavras-chave',
  '选择工作区': 'Selecionar espaço de trabalho',
  '暂无描述': 'Sem descrição',
  '配置': 'Configurar',
  '查看': 'Ver',
  '暂无协议': 'Nenhum protocolo',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Nenhum protocolo disponível. Crie a partir de modelos embutidos ou adicione um personalizado.',
  'v1.2.4 - 已启用': 'v1.2.4 - Habilitado',
  '已启用': 'Habilitado',
  'MQTT 适配器': 'Adaptador MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - Não instalado',
  '未安装': 'Não instalado',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Nenhum item configurável. As configurações de execução ficarão disponíveis conforme os módulos se expandirem.',
  '日志采集与归档策略将在后续版本中提供。': 'Políticas de coleta e arquivamento de logs estarão disponíveis em uma versão futura.',
  '串口配置': 'Configuração serial',
  '新建通道': 'Novo canal',
  '配置串口连接参数': 'Configurar parâmetros de conexão serial',
  '配置新的通信连接参数': 'Configurar novos parâmetros de conexão',
  '串口 (Serial)': 'Serial (Serial)',
  'TCP / 网络': 'TCP / Rede',
  '基本信息': 'Informações básicas',
  '通道名称': 'Nome do canal',
  '例如：传感器A接口': 'Exemplo: interface do sensor A',
  '串口端口': 'Porta serial',
  '选择串口': 'Selecionar porta serial',
  '无可用串口': 'Nenhuma porta serial disponível',
  '目标地址': 'Endereço de destino',
  '例如：192.168.1.10': 'Exemplo: 192.168.1.10',
  '串口参数': 'Parâmetros seriais',
  '波特率': 'Taxa de baud',
  '数据位': 'Bits de dados',
  '停止位': 'Bits de parada',
  '校验位': 'Paridade',
  '无校验': 'Sem paridade',
  '奇校验': 'Paridade ímpar',
  '偶校验': 'Paridade par',
  '流控': 'Controle de fluxo',
  '无': 'Nenhum',
  '读超时 (ms)': 'Tempo limite de leitura (ms)',
  '写超时 (ms)': 'Tempo limite de escrita (ms)',
  'TCP 端口': 'Porta TCP',
  '保存后立即连接': 'Conectar após salvar',
  '创建后立即启动连接': 'Iniciar conexão após a criação',
  '取消': 'Cancelar',
  '保存配置': 'Salvar configuração',
  '创建通道': 'Criar canal',
  '新建协议': 'Novo protocolo',
  '配置协议': 'Configurar protocolo',
  '协议详情': 'Detalhes do protocolo',
  '添加自定义协议元数据，供解析引擎识别。': 'Adicionar metadados de protocolo personalizados para que o motor de análise reconheça.',
  '查看或更新协议描述与分类。': 'Ver ou atualizar a descrição e a categoria do protocolo.',
  '协议名称': 'Nome do protocolo',
  '状态': 'Status',
  '描述': 'Descrição',
  '驱动类': 'Classe do driver',
  '保存': 'Salvar',
  '删除协议': 'Excluir protocolo',
  '确认删除自定义协议': 'Confirmar exclusão do protocolo personalizado',
  '吗？': '?',
  '确认删除': 'Confirmar exclusão',
  'UI YAML 预览': 'Pré-visualização de UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Mostrar renderização da UI enquanto o script é executado',
  '解析失败': 'Falha na análise',
  '暂无可渲染的 UI 配置': 'Nenhuma configuração de UI renderizável',
}
const ruRU = {
  ...enUS,
  'nav.manual': 'Последовательный терминал',
  'nav.scripts': 'Скрипты автоматизации',
  'nav.proxy': 'Монитор прокси',
  'nav.protocols': 'Менеджер протоколов',
  'nav.settings': 'Настройки',
  'nav.workspace': 'Рабочее пространство администратора',
  'status.connected': 'Подключено',
  'status.connecting': 'Подключение',
  'status.error': 'Ошибка',
  'status.disconnected': 'Отключено',
  'theme.system': 'Система',
  'theme.dark': 'Темная (Инженер)',
  'theme.light': 'Светлая',
  'header.protocols.title': 'Менеджер протоколов',
  'header.protocols.desc': 'Определяйте протоколы, привязывайте каналы и настраивайте правила разбора.',
  'action.refresh': 'Обновить',
  'action.createProtocol': 'Новый протокол',
  'protocol.tab.all': 'Все протоколы',
  'protocol.tab.custom': 'Пользовательский',
  'header.settings.title': 'Настройки приложения',
  'header.settings.desc': 'Управление глобальными предпочтениями, значениями по умолчанию и конфигурацией выполнения.',
  'action.discardChanges': 'Отменить изменения',
  'action.saveChanges': 'Сохранить изменения',
  'settings.tab.general': 'Общие',
  'settings.tab.plugins': 'Плагины',
  'settings.tab.runtime': 'Выполнение',
  'settings.tab.logs': 'Журналы',
  'settings.language': 'Язык',
  'settings.theme': 'Тема',
  'settings.autoConnect.title': 'Автоподключение при запуске',
  'settings.autoConnect.desc': 'Автоматически переподключаться к последнему активному каналу.',
  'settings.workspace': 'Рабочее пространство',
  'settings.chooseFolder': 'Выбрать папку',
  'settings.plugins.title': 'Плагины',
  'settings.plugins.refresh': 'Обновить список',
  '空闲': 'Простой',
  '串口通道': 'Последовательный канал',
  'TCP 客户端': 'TCP-клиент',
  'TCP 服务端': 'TCP-сервер',
  '端口': 'Порт',
  '运行中': 'Выполняется',
  '请输入指令名称和内容': 'Введите имя и содержимое команды',
  '协议': 'Протокол',
  '可用': 'Доступно',
  '自定义': 'Пользовательский',
  '已禁用': 'Отключено',
  '未知': 'Неизвестно',
  '键名': 'Ключ',
  '驱动': 'Драйвер',
  '分类': 'Категория',
  '搜索关键词': 'Поиск по ключевым словам',
  '选择工作区': 'Выбрать рабочее пространство',
  '暂无描述': 'Нет описания',
  '配置': 'Настроить',
  '查看': 'Просмотреть',
  '暂无协议': 'Нет протоколов',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Протоколы отсутствуют. Создайте из встроенных шаблонов или добавьте пользовательский.',
  'v1.2.4 - 已启用': 'v1.2.4 - Включено',
  '已启用': 'Включено',
  'MQTT 适配器': 'MQTT-адаптер',
  'v0.9.8 - 未安装': 'v0.9.8 - Не установлено',
  '未安装': 'Не установлено',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Нет настраиваемых элементов. Настройки выполнения будут доступны по мере расширения модулей.',
  '日志采集与归档策略将在后续版本中提供。': 'Политики сбора и архивирования журналов будут доступны в будущей версии.',
  '串口配置': 'Конфигурация последовательного порта',
  '新建通道': 'Новый канал',
  '配置串口连接参数': 'Настроить параметры последовательного соединения',
  '配置新的通信连接参数': 'Настроить новые параметры соединения',
  '串口 (Serial)': 'Последовательный (Serial)',
  'TCP / 网络': 'TCP / Сеть',
  '基本信息': 'Основная информация',
  '通道名称': 'Имя канала',
  '例如：传感器A接口': 'Пример: интерфейс датчика A',
  '串口端口': 'Последовательный порт',
  '选择串口': 'Выбрать последовательный порт',
  '无可用串口': 'Нет доступных последовательных портов',
  '目标地址': 'Целевой адрес',
  '例如：192.168.1.10': 'Пример: 192.168.1.10',
  '串口参数': 'Параметры последовательного порта',
  '波特率': 'Скорость (бод)',
  '数据位': 'Биты данных',
  '停止位': 'Стоп-биты',
  '校验位': 'Четность',
  '无校验': 'Без четности',
  '奇校验': 'Нечетная четность',
  '偶校验': 'Четная четность',
  '流控': 'Управление потоком',
  '无': 'Нет',
  '读超时 (ms)': 'Тайм-аут чтения (мс)',
  '写超时 (ms)': 'Тайм-аут записи (мс)',
  'TCP 端口': 'TCP-порт',
  '保存后立即连接': 'Подключить после сохранения',
  '创建后立即启动连接': 'Запустить подключение после создания',
  '取消': 'Отмена',
  '保存配置': 'Сохранить конфигурацию',
  '创建通道': 'Создать канал',
  '新建协议': 'Новый протокол',
  '配置协议': 'Настроить протокол',
  '协议详情': 'Сведения о протоколе',
  '添加自定义协议元数据，供解析引擎识别。': 'Добавить метаданные пользовательского протокола для распознавания движком.',
  '查看或更新协议描述与分类。': 'Просмотреть или обновить описание и категорию протокола.',
  '协议名称': 'Имя протокола',
  '状态': 'Статус',
  '描述': 'Описание',
  '驱动类': 'Класс драйвера',
  '保存': 'Сохранить',
  '删除协议': 'Удалить протокол',
  '确认删除自定义协议': 'Подтвердить удаление пользовательского протокола',
  '吗？': '?',
  '确认删除': 'Подтвердить удаление',
  'UI YAML 预览': 'Предпросмотр UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Показывать рендеринг UI во время выполнения скрипта',
  '解析失败': 'Ошибка разбора',
  '暂无可渲染的 UI 配置': 'Нет конфигурации UI для рендера',
}
const ar = {
  ...enUS,
  'nav.manual': 'طرفية تسلسلية',
  'nav.scripts': 'نصوص الأتمتة',
  'nav.proxy': 'مراقب الوكيل',
  'nav.protocols': 'مدير البروتوكولات',
  'nav.settings': 'الإعدادات',
  'nav.workspace': 'مساحة عمل المسؤول',
  'status.connected': 'متصل',
  'status.connecting': 'جارٍ الاتصال',
  'status.error': 'خطأ',
  'status.disconnected': 'غير متصل',
  'theme.system': 'النظام',
  'theme.dark': 'داكن (مهندس)',
  'theme.light': 'فاتح',
  'header.protocols.title': 'مدير البروتوكولات',
  'header.protocols.desc': 'عرّف البروتوكولات، واربط القنوات، واضبط قواعد التحليل.',
  'action.refresh': 'تحديث',
  'action.createProtocol': 'بروتوكول جديد',
  'protocol.tab.all': 'كل البروتوكولات',
  'protocol.tab.custom': 'مخصص',
  'header.settings.title': 'إعدادات التطبيق',
  'header.settings.desc': 'إدارة التفضيلات العامة والقيم الافتراضية وتكوين وقت التشغيل.',
  'action.discardChanges': 'تجاهل التغييرات',
  'action.saveChanges': 'حفظ التغييرات',
  'settings.tab.general': 'عام',
  'settings.tab.plugins': 'الإضافات',
  'settings.tab.runtime': 'وقت التشغيل',
  'settings.tab.logs': 'السجلات',
  'settings.language': 'اللغة',
  'settings.theme': 'السمة',
  'settings.autoConnect.title': 'اتصال تلقائي عند التشغيل',
  'settings.autoConnect.desc': 'إعادة الاتصال تلقائياً بآخر قناة نشطة.',
  'settings.workspace': 'مساحة العمل',
  'settings.chooseFolder': 'اختر مجلداً',
  'settings.plugins.title': 'الإضافات',
  'settings.plugins.refresh': 'تحديث القائمة',
  '空闲': 'خامل',
  '串口通道': 'قناة تسلسلية',
  'TCP 客户端': 'عميل TCP',
  'TCP 服务端': 'خادم TCP',
  '端口': 'منفذ',
  '运行中': 'قيد التشغيل',
  '请输入指令名称和内容': 'أدخل اسم الأمر ومحتواه',
  '协议': 'بروتوكول',
  '可用': 'متاح',
  '自定义': 'مخصص',
  '已禁用': 'معطل',
  '未知': 'غير معروف',
  '键名': 'مفتاح',
  '驱动': 'برنامج تشغيل',
  '分类': 'فئة',
  '搜索关键词': 'ابحث عن كلمات مفتاحية',
  '选择工作区': 'اختر مساحة العمل',
  '暂无描述': 'لا وصف',
  '配置': 'تهيئة',
  '查看': 'عرض',
  '暂无协议': 'لا توجد بروتوكولات',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'لا توجد بروتوكولات متاحة. أنشئ من القوالب المضمنة أو أضف مخصصاً.',
  'v1.2.4 - 已启用': 'v1.2.4 - مفعّل',
  '已启用': 'مفعّل',
  'MQTT 适配器': 'محوّل MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - غير مثبت',
  '未安装': 'غير مثبت',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'لا توجد عناصر قابلة للتهيئة. ستتوفر إعدادات وقت التشغيل مع توسع الوحدات.',
  '日志采集与归档策略将在后续版本中提供。': 'ستتوفر سياسات جمع السجلات وأرشفتها في إصدار لاحق.',
  '串口配置': 'تهيئة تسلسلية',
  '新建通道': 'قناة جديدة',
  '配置串口连接参数': 'تهيئة معلمات الاتصال التسلسلي',
  '配置新的通信连接参数': 'تهيئة معلمات الاتصال الجديدة',
  '串口 (Serial)': 'تسلسلي (Serial)',
  'TCP / 网络': 'TCP / الشبكة',
  '基本信息': 'معلومات أساسية',
  '通道名称': 'اسم القناة',
  '例如：传感器A接口': 'مثال: واجهة المستشعر A',
  '串口端口': 'منفذ تسلسلي',
  '选择串口': 'اختر منفذًا تسلسليًا',
  '无可用串口': 'لا توجد منافذ تسلسلية متاحة',
  '目标地址': 'عنوان الهدف',
  '例如：192.168.1.10': 'مثال: 192.168.1.10',
  '串口参数': 'معلمات التسلسل',
  '波特率': 'معدل البود',
  '数据位': 'بتات البيانات',
  '停止位': 'بتات التوقف',
  '校验位': 'التماثل',
  '无校验': 'بدون تماثل',
  '奇校验': 'تماثل فردي',
  '偶校验': 'تماثل زوجي',
  '流控': 'التحكم في التدفق',
  '无': 'لا شيء',
  '读超时 (ms)': 'مهلة القراءة (ms)',
  '写超时 (ms)': 'مهلة الكتابة (ms)',
  'TCP 端口': 'منفذ TCP',
  '保存后立即连接': 'الاتصال بعد الحفظ',
  '创建后立即启动连接': 'بدء الاتصال بعد الإنشاء',
  '取消': 'إلغاء',
  '保存配置': 'حفظ التهيئة',
  '创建通道': 'إنشاء قناة',
  '新建协议': 'بروتوكول جديد',
  '配置协议': 'تهيئة البروتوكول',
  '协议详情': 'تفاصيل البروتوكول',
  '添加自定义协议元数据，供解析引擎识别。': 'أضف بيانات تعريف بروتوكول مخصصة ليتعرف عليها محرك التحليل.',
  '查看或更新协议描述与分类。': 'عرض أو تحديث وصف البروتوكول وفئته.',
  '协议名称': 'اسم البروتوكول',
  '状态': 'الحالة',
  '描述': 'الوصف',
  '驱动类': 'فئة برنامج التشغيل',
  '保存': 'حفظ',
  '删除协议': 'حذف البروتوكول',
  '确认删除自定义协议': 'تأكيد حذف البروتوكول المخصص',
  '吗？': '؟',
  '确认删除': 'تأكيد الحذف',
  'UI YAML 预览': 'معاينة UI YAML',
  '脚本运行中展示 UI 渲染结果': 'عرض ناتج عرض UI أثناء تشغيل السكربت',
  '解析失败': 'فشل التحليل',
  '暂无可渲染的 UI 配置': 'لا توجد تهيئة UI قابلة للعرض',
}
const hi = {
  ...enUS,
  'nav.manual': 'सीरियल टर्मिनल',
  'nav.scripts': 'ऑटोमेशन स्क्रिप्ट्स',
  'nav.proxy': 'प्रॉक्सी मॉनिटर',
  'nav.protocols': 'प्रोटोकॉल मैनेजर',
  'nav.settings': 'सेटिंग्स',
  'nav.workspace': 'एडमिन वर्कस्पेस',
  'status.connected': 'कनेक्टेड',
  'status.connecting': 'कनेक्ट हो रहा है',
  'status.error': 'त्रुटि',
  'status.disconnected': 'डिसकनेक्टेड',
  'theme.system': 'सिस्टम',
  'theme.dark': 'डार्क (इंजीनियर)',
  'theme.light': 'लाइट',
  'header.protocols.title': 'प्रोटोकॉल मैनेजर',
  'header.protocols.desc': 'प्रोटोकॉल परिभाषित करें, चैनल बाँधें और पार्सिंग नियम कॉन्फ़िगर करें।',
  'action.refresh': 'रीफ़्रेश',
  'action.createProtocol': 'नया प्रोटोकॉल',
  'protocol.tab.all': 'सभी प्रोटोकॉल',
  'protocol.tab.custom': 'कस्टम',
  'header.settings.title': 'ऐप सेटिंग्स',
  'header.settings.desc': 'वैश्विक प्राथमिकताएँ, डिफ़ॉल्ट और रनटाइम कॉन्फ़िगरेशन प्रबंधित करें।',
  'action.discardChanges': 'परिवर्तन त्यागें',
  'action.saveChanges': 'परिवर्तन सहेजें',
  'settings.tab.general': 'सामान्य',
  'settings.tab.plugins': 'प्लगइन्स',
  'settings.tab.runtime': 'रनटाइम',
  'settings.tab.logs': 'लॉग्स',
  'settings.language': 'भाषा',
  'settings.theme': 'थीम',
  'settings.autoConnect.title': 'लॉन्च पर ऑटो-कनेक्ट',
  'settings.autoConnect.desc': 'आख़िरी सक्रिय चैनल से स्वतः पुनः कनेक्ट करें।',
  'settings.workspace': 'वर्कस्पेस',
  'settings.chooseFolder': 'फ़ोल्डर चुनें',
  'settings.plugins.title': 'प्लगइन्स',
  'settings.plugins.refresh': 'सूची रीफ़्रेश करें',
  '空闲': 'निष्क्रिय',
  '串口通道': 'सीरियल चैनल',
  'TCP 客户端': 'TCP क्लाइंट',
  'TCP 服务端': 'TCP सर्वर',
  '端口': 'पोर्ट',
  '运行中': 'चल रहा है',
  '请输入指令名称和内容': 'कमांड का नाम और सामग्री दर्ज करें',
  '协议': 'प्रोटोकॉल',
  '可用': 'उपलब्ध',
  '自定义': 'कस्टम',
  '已禁用': 'अक्षम',
  '未知': 'अज्ञात',
  '键名': 'कुंजी',
  '驱动': 'ड्राइवर',
  '分类': 'श्रेणी',
  '搜索关键词': 'कीवर्ड खोजें',
  '选择工作区': 'वर्कस्पेस चुनें',
  '暂无描述': 'कोई विवरण नहीं',
  '配置': 'कॉन्फ़िगर करें',
  '查看': 'देखें',
  '暂无协议': 'कोई प्रोटोकॉल नहीं',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'कोई प्रोटोकॉल उपलब्ध नहीं। अंतर्निर्मित टेम्पलेट से बनाएं या कस्टम जोड़ें।',
  'v1.2.4 - 已启用': 'v1.2.4 - सक्षम',
  '已启用': 'सक्षम',
  'MQTT 适配器': 'MQTT एडेप्टर',
  'v0.9.8 - 未安装': 'v0.9.8 - इंस्टॉल नहीं',
  '未安装': 'इंस्टॉल नहीं',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'कोई कॉन्फ़िगर करने योग्य आइटम नहीं। मॉड्यूल बढ़ने पर रनटाइम सेटिंग्स उपलब्ध होंगी।',
  '日志采集与归档策略将在后续版本中提供。': 'लॉग संग्रह और संग्रहण नीतियाँ भविष्य के संस्करण में उपलब्ध होंगी।',
  '串口配置': 'सीरियल कॉन्फ़िगरेशन',
  '新建通道': 'नया चैनल',
  '配置串口连接参数': 'सीरियल कनेक्शन पैरामीटर कॉन्फ़िगर करें',
  '配置新的通信连接参数': 'नए संचार कनेक्शन पैरामीटर कॉन्फ़िगर करें',
  '串口 (Serial)': 'सीरियल (Serial)',
  'TCP / 网络': 'TCP / नेटवर्क',
  '基本信息': 'मूल जानकारी',
  '通道名称': 'चैनल नाम',
  '例如：传感器A接口': 'उदाहरण: सेंसर A इंटरफ़ेस',
  '串口端口': 'सीरियल पोर्ट',
  '选择串口': 'सीरियल पोर्ट चुनें',
  '无可用串口': 'कोई सीरियल पोर्ट उपलब्ध नहीं',
  '目标地址': 'लक्ष्य पता',
  '例如：192.168.1.10': 'उदाहरण: 192.168.1.10',
  '串口参数': 'सीरियल पैरामीटर',
  '波特率': 'बॉड रेट',
  '数据位': 'डेटा बिट्स',
  '停止位': 'स्टॉप बिट्स',
  '校验位': 'पैरिटी',
  '无校验': 'कोई पैरिटी नहीं',
  '奇校验': 'विषम पैरिटी',
  '偶校验': 'सम पैरिटी',
  '流控': 'फ़्लो कंट्रोल',
  '无': 'कोई नहीं',
  '读超时 (ms)': 'रीड टाइमआउट (ms)',
  '写超时 (ms)': 'राइट टाइमआउट (ms)',
  'TCP 端口': 'TCP पोर्ट',
  '保存后立即连接': 'सहेजने के बाद कनेक्ट करें',
  '创建后立即启动连接': 'निर्माण के बाद कनेक्शन शुरू करें',
  '取消': 'रद्द करें',
  '保存配置': 'कॉन्फ़िगरेशन सहेजें',
  '创建通道': 'चैनल बनाएँ',
  '新建协议': 'नया प्रोटोकॉल',
  '配置协议': 'प्रोटोकॉल कॉन्फ़िगर करें',
  '协议详情': 'प्रोटोकॉल विवरण',
  '添加自定义协议元数据，供解析引擎识别。': 'पार्सर इंजन के लिए कस्टम प्रोटोकॉल मेटाडेटा जोड़ें।',
  '查看或更新协议描述与分类。': 'प्रोटोकॉल विवरण और श्रेणी देखें या अपडेट करें।',
  '协议名称': 'प्रोटोकॉल नाम',
  '状态': 'स्थिति',
  '描述': 'विवरण',
  '驱动类': 'ड्राइवर क्लास',
  '保存': 'सहेजें',
  '删除协议': 'प्रोटोकॉल हटाएँ',
  '确认删除自定义协议': 'कस्टम प्रोटोकॉल हटाने की पुष्टि करें',
  '吗？': '?',
  '确认删除': 'हटाने की पुष्टि',
  'UI YAML 预览': 'UI YAML प्रीव्यू',
  '脚本运行中展示 UI 渲染结果': 'स्क्रिप्ट चलने के दौरान UI रेंडरिंग दिखाएँ',
  '解析失败': 'पार्स विफल',
  '暂无可渲染的 UI 配置': 'कोई UI कॉन्फ़िगरेशन रेंडर करने योग्य नहीं',
}
const itIT = {
  ...enUS,
  'nav.manual': 'Terminale seriale',
  'nav.scripts': 'Script di automazione',
  'nav.proxy': 'Monitor proxy',
  'nav.protocols': 'Gestore protocolli',
  'nav.settings': 'Impostazioni',
  'nav.workspace': 'Area di lavoro admin',
  'status.connected': 'Connesso',
  'status.connecting': 'Connessione in corso',
  'status.error': 'Errore',
  'status.disconnected': 'Disconnesso',
  'theme.system': 'Sistema',
  'theme.dark': 'Scuro (Ingegnere)',
  'theme.light': 'Chiaro',
  'header.protocols.title': 'Gestore protocolli',
  'header.protocols.desc': 'Definisci i protocolli, associa i canali e configura le regole di parsing.',
  'action.refresh': 'Aggiorna',
  'action.createProtocol': 'Nuovo protocollo',
  'protocol.tab.all': 'Tutti i protocolli',
  'protocol.tab.custom': 'Personalizzato',
  'header.settings.title': 'Impostazioni app',
  'header.settings.desc': 'Gestisci preferenze globali, valori predefiniti e configurazione di runtime.',
  'action.discardChanges': 'Annulla modifiche',
  'action.saveChanges': 'Salva modifiche',
  'settings.tab.general': 'Generale',
  'settings.tab.plugins': 'Plugin',
  'settings.tab.runtime': 'Runtime',
  'settings.tab.logs': 'Log',
  'settings.language': 'Lingua',
  'settings.theme': 'Tema',
  'settings.autoConnect.title': 'Connessione automatica all’avvio',
  'settings.autoConnect.desc': 'Riconnetti automaticamente l’ultimo canale attivo.',
  'settings.workspace': 'Area di lavoro',
  'settings.chooseFolder': 'Scegli cartella',
  'settings.plugins.title': 'Plugin',
  'settings.plugins.refresh': 'Aggiorna elenco',
  '空闲': 'Inattivo',
  '串口通道': 'Canale seriale',
  'TCP 客户端': 'Client TCP',
  'TCP 服务端': 'Server TCP',
  '端口': 'Porta',
  '运行中': 'In esecuzione',
  '请输入指令名称和内容': 'Inserisci nome e contenuto del comando',
  '协议': 'Protocollo',
  '可用': 'Disponibile',
  '自定义': 'Personalizzato',
  '已禁用': 'Disabilitato',
  '未知': 'Sconosciuto',
  '键名': 'Chiave',
  '驱动': 'Driver',
  '分类': 'Categoria',
  '搜索关键词': 'Cerca parole chiave',
  '选择工作区': 'Seleziona area di lavoro',
  '暂无描述': 'Nessuna descrizione',
  '配置': 'Configura',
  '查看': 'Visualizza',
  '暂无协议': 'Nessun protocollo',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Nessun protocollo disponibile. Crea da modelli integrati o aggiungi un personalizzato.',
  'v1.2.4 - 已启用': 'v1.2.4 - Abilitato',
  '已启用': 'Abilitato',
  'MQTT 适配器': 'Adattatore MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - Non installato',
  '未安装': 'Non installato',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Nessun elemento configurabile. Le impostazioni runtime saranno disponibili con l’espansione dei moduli.',
  '日志采集与归档策略将在后续版本中提供。': 'Le politiche di raccolta e archiviazione dei log saranno disponibili in una versione futura.',
  '串口配置': 'Configurazione seriale',
  '新建通道': 'Nuovo canale',
  '配置串口连接参数': 'Configura i parametri di connessione seriale',
  '配置新的通信连接参数': 'Configura i nuovi parametri di connessione',
  '串口 (Serial)': 'Seriale (Serial)',
  'TCP / 网络': 'TCP / Rete',
  '基本信息': 'Informazioni di base',
  '通道名称': 'Nome canale',
  '例如：传感器A接口': 'Esempio: interfaccia sensore A',
  '串口端口': 'Porta seriale',
  '选择串口': 'Seleziona porta seriale',
  '无可用串口': 'Nessuna porta seriale disponibile',
  '目标地址': 'Indirizzo di destinazione',
  '例如：192.168.1.10': 'Esempio: 192.168.1.10',
  '串口参数': 'Parametri seriali',
  '波特率': 'Baud rate',
  '数据位': 'Bit di dati',
  '停止位': 'Bit di stop',
  '校验位': 'Parità',
  '无校验': 'Nessuna parità',
  '奇校验': 'Parità dispari',
  '偶校验': 'Parità pari',
  '流控': 'Controllo di flusso',
  '无': 'Nessuno',
  '读超时 (ms)': 'Timeout lettura (ms)',
  '写超时 (ms)': 'Timeout scrittura (ms)',
  'TCP 端口': 'Porta TCP',
  '保存后立即连接': 'Connetti dopo il salvataggio',
  '创建后立即启动连接': 'Avvia la connessione dopo la creazione',
  '取消': 'Annulla',
  '保存配置': 'Salva configurazione',
  '创建通道': 'Crea canale',
  '新建协议': 'Nuovo protocollo',
  '配置协议': 'Configura protocollo',
  '协议详情': 'Dettagli protocollo',
  '添加自定义协议元数据，供解析引擎识别。': 'Aggiungi metadati di protocollo personalizzati per il motore di parsing.',
  '查看或更新协议描述与分类。': 'Visualizza o aggiorna descrizione e categoria del protocollo.',
  '协议名称': 'Nome protocollo',
  '状态': 'Stato',
  '描述': 'Descrizione',
  '驱动类': 'Classe driver',
  '保存': 'Salva',
  '删除协议': 'Elimina protocollo',
  '确认删除自定义协议': 'Conferma eliminazione protocollo personalizzato',
  '吗？': '?',
  '确认删除': 'Conferma eliminazione',
  'UI YAML 预览': 'Anteprima UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Mostra il rendering UI durante l’esecuzione dello script',
  '解析失败': 'Analisi non riuscita',
  '暂无可渲染的 UI 配置': 'Nessuna configurazione UI renderizzabile',
}
const nlNL = {
  ...enUS,
  'nav.manual': 'Seriële terminal',
  'nav.scripts': 'Automatiseringsscripts',
  'nav.proxy': 'Proxy-monitor',
  'nav.protocols': 'Protocolbeheer',
  'nav.settings': 'Instellingen',
  'nav.workspace': 'Admin-werkruimte',
  'status.connected': 'Verbonden',
  'status.connecting': 'Bezig met verbinden',
  'status.error': 'Fout',
  'status.disconnected': 'Niet verbonden',
  'theme.system': 'Systeem',
  'theme.dark': 'Donker (Engineer)',
  'theme.light': 'Licht',
  'header.protocols.title': 'Protocolbeheer',
  'header.protocols.desc': 'Definieer protocollen, koppel kanalen en configureer parse-regels.',
  'action.refresh': 'Vernieuwen',
  'action.createProtocol': 'Nieuw protocol',
  'protocol.tab.all': 'Alle protocollen',
  'protocol.tab.custom': 'Aangepast',
  'header.settings.title': 'App-instellingen',
  'header.settings.desc': 'Beheer globale voorkeuren, standaardwaarden en runtimeconfiguratie.',
  'action.discardChanges': 'Wijzigingen verwerpen',
  'action.saveChanges': 'Wijzigingen opslaan',
  'settings.tab.general': 'Algemeen',
  'settings.tab.plugins': 'Plugins',
  'settings.tab.runtime': 'Runtime',
  'settings.tab.logs': 'Logboeken',
  'settings.language': 'Taal',
  'settings.theme': 'Thema',
  'settings.autoConnect.title': 'Automatisch verbinden bij starten',
  'settings.autoConnect.desc': 'Automatisch opnieuw verbinden met het laatst actieve kanaal.',
  'settings.workspace': 'Werkruimte',
  'settings.chooseFolder': 'Map kiezen',
  'settings.plugins.title': 'Plugins',
  'settings.plugins.refresh': 'Lijst vernieuwen',
  '空闲': 'Inactief',
  '串口通道': 'Serieel kanaal',
  'TCP 客户端': 'TCP-client',
  'TCP 服务端': 'TCP-server',
  '端口': 'Poort',
  '运行中': 'Actief',
  '请输入指令名称和内容': 'Voer de opdrachtnaam en inhoud in',
  '协议': 'Protocol',
  '可用': 'Beschikbaar',
  '自定义': 'Aangepast',
  '已禁用': 'Uitgeschakeld',
  '未知': 'Onbekend',
  '键名': 'Sleutel',
  '驱动': 'Driver',
  '分类': 'Categorie',
  '搜索关键词': 'Zoek trefwoorden',
  '选择工作区': 'Werkruimte kiezen',
  '暂无描述': 'Geen beschrijving',
  '配置': 'Configureren',
  '查看': 'Bekijken',
  '暂无协议': 'Geen protocollen',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Geen protocollen beschikbaar. Maak aan vanuit ingebouwde sjablonen of voeg een aangepast protocol toe.',
  'v1.2.4 - 已启用': 'v1.2.4 - Ingeschakeld',
  '已启用': 'Ingeschakeld',
  'MQTT 适配器': 'MQTT-adapter',
  'v0.9.8 - 未安装': 'v0.9.8 - Niet geïnstalleerd',
  '未安装': 'Niet geïnstalleerd',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Geen configureerbare items. Runtime-instellingen worden beschikbaar naarmate modules uitbreiden.',
  '日志采集与归档策略将在后续版本中提供。': 'Beleid voor logverzameling en archivering is beschikbaar in een toekomstige release.',
  '串口配置': 'Seriële configuratie',
  '新建通道': 'Nieuw kanaal',
  '配置串口连接参数': 'Seriële verbindingsparameters configureren',
  '配置新的通信连接参数': 'Nieuwe verbindingsparameters configureren',
  '串口 (Serial)': 'Serieel (Serial)',
  'TCP / 网络': 'TCP / Netwerk',
  '基本信息': 'Basisinformatie',
  '通道名称': 'Kanaalnaam',
  '例如：传感器A接口': 'Voorbeeld: sensor A-interface',
  '串口端口': 'Seriële poort',
  '选择串口': 'Seriële poort selecteren',
  '无可用串口': 'Geen beschikbare seriële poorten',
  '目标地址': 'Doeladres',
  '例如：192.168.1.10': 'Voorbeeld: 192.168.1.10',
  '串口参数': 'Seriële parameters',
  '波特率': 'Baudsnelheid',
  '数据位': 'Databits',
  '停止位': 'Stopbits',
  '校验位': 'Pariteit',
  '无校验': 'Geen pariteit',
  '奇校验': 'Oneven pariteit',
  '偶校验': 'Even pariteit',
  '流控': 'Flow control',
  '无': 'Geen',
  '读超时 (ms)': 'Lees-timeout (ms)',
  '写超时 (ms)': 'Schrijf-timeout (ms)',
  'TCP 端口': 'TCP-poort',
  '保存后立即连接': 'Verbinden na opslaan',
  '创建后立即启动连接': 'Verbinding starten na aanmaken',
  '取消': 'Annuleren',
  '保存配置': 'Configuratie opslaan',
  '创建通道': 'Kanaal maken',
  '新建协议': 'Nieuw protocol',
  '配置协议': 'Protocol configureren',
  '协议详情': 'Protocoldetails',
  '添加自定义协议元数据，供解析引擎识别。': 'Aangepaste protocolmetadata toevoegen zodat de parser-engine deze herkent.',
  '查看或更新协议描述与分类。': 'Protocolbeschrijving en categorie bekijken of bijwerken.',
  '协议名称': 'Protocolnaam',
  '状态': 'Status',
  '描述': 'Beschrijving',
  '驱动类': 'Driver-klasse',
  '保存': 'Opslaan',
  '删除协议': 'Protocol verwijderen',
  '确认删除自定义协议': 'Bevestig verwijderen van aangepast protocol',
  '吗？': '?',
  '确认删除': 'Verwijderen bevestigen',
  'UI YAML 预览': 'UI YAML-voorvertoning',
  '脚本运行中展示 UI 渲染结果': 'UI-rendering tonen tijdens het uitvoeren van het script',
  '解析失败': 'Parseren mislukt',
  '暂无可渲染的 UI 配置': 'Geen renderbare UI-configuratie',
}
const thTH = {
  ...enUS,
  'nav.manual': 'เทอร์มินัลอนุกรม',
  'nav.scripts': 'สคริปต์อัตโนมัติ',
  'nav.proxy': 'มอนิเตอร์พร็อกซี',
  'nav.protocols': 'ตัวจัดการโปรโตคอล',
  'nav.settings': 'การตั้งค่า',
  'nav.workspace': 'เวิร์กสเปซผู้ดูแล',
  'status.connected': 'เชื่อมต่อแล้ว',
  'status.connecting': 'กำลังเชื่อมต่อ',
  'status.error': 'ข้อผิดพลาด',
  'status.disconnected': 'ยกเลิกการเชื่อมต่อ',
  'theme.system': 'ระบบ',
  'theme.dark': 'มืด (วิศวกร)',
  'theme.light': 'สว่าง',
  'header.protocols.title': 'ตัวจัดการโปรโตคอล',
  'header.protocols.desc': 'กำหนดโปรโตคอล ผูกช่องทาง และกำหนดกฎการแยกวิเคราะห์',
  'action.refresh': 'รีเฟรช',
  'action.createProtocol': 'โปรโตคอลใหม่',
  'protocol.tab.all': 'โปรโตคอลทั้งหมด',
  'protocol.tab.custom': 'กำหนดเอง',
  'header.settings.title': 'การตั้งค่าแอป',
  'header.settings.desc': 'จัดการค่ากำหนดทั่วไประดับโลก ค่าเริ่มต้น และการกำหนดค่าขณะทำงาน',
  'action.discardChanges': 'ยกเลิกการเปลี่ยนแปลง',
  'action.saveChanges': 'บันทึกการเปลี่ยนแปลง',
  'settings.tab.general': 'ทั่วไป',
  'settings.tab.plugins': 'ปลั๊กอิน',
  'settings.tab.runtime': 'ขณะทำงาน',
  'settings.tab.logs': 'บันทึก',
  'settings.language': 'ภาษา',
  'settings.theme': 'ธีม',
  'settings.autoConnect.title': 'เชื่อมต่ออัตโนมัติเมื่อเปิด',
  'settings.autoConnect.desc': 'เชื่อมต่อกับช่องทางที่ใช้งานล่าสุดโดยอัตโนมัติ',
  'settings.workspace': 'เวิร์กสเปซ',
  'settings.chooseFolder': 'เลือกโฟลเดอร์',
  'settings.plugins.title': 'ปลั๊กอิน',
  'settings.plugins.refresh': 'รีเฟรชรายการ',
  '空闲': 'ว่าง',
  '串口通道': 'ช่องทางอนุกรม',
  'TCP 客户端': 'ไคลเอนต์ TCP',
  'TCP 服务端': 'เซิร์ฟเวอร์ TCP',
  '端口': 'พอร์ต',
  '运行中': 'กำลังทำงาน',
  '请输入指令名称和内容': 'ป้อนชื่อคำสั่งและเนื้อหา',
  '协议': 'โปรโตคอล',
  '可用': 'พร้อมใช้งาน',
  '自定义': 'กำหนดเอง',
  '已禁用': 'ปิดใช้งาน',
  '未知': 'ไม่ทราบ',
  '键名': 'คีย์',
  '驱动': 'ไดรเวอร์',
  '分类': 'หมวดหมู่',
  '搜索关键词': 'ค้นหาคีย์เวิร์ด',
  '选择工作区': 'เลือกเวิร์กสเปซ',
  '暂无描述': 'ไม่มีคำอธิบาย',
  '配置': 'กำหนดค่า',
  '查看': 'ดู',
  '暂无协议': 'ไม่มีโปรโตคอล',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'ไม่มีโปรโตคอลที่ใช้ได้ สร้างจากเทมเพลตในตัวหรือเพิ่มแบบกำหนดเอง',
  'v1.2.4 - 已启用': 'v1.2.4 - เปิดใช้งาน',
  '已启用': 'เปิดใช้งาน',
  'MQTT 适配器': 'อะแดปเตอร์ MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - ยังไม่ได้ติดตั้ง',
  '未安装': 'ยังไม่ได้ติดตั้ง',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'ไม่มีรายการที่กำหนดค่าได้ การตั้งค่าขณะทำงานจะพร้อมใช้งานเมื่อโมดูลขยาย',
  '日志采集与归档策略将在后续版本中提供。': 'นโยบายการเก็บรวบรวมและการจัดเก็บบันทึกจะมีในเวอร์ชันถัดไป',
  '串口配置': 'การกำหนดค่าอนุกรม',
  '新建通道': 'ช่องทางใหม่',
  '配置串口连接参数': 'กำหนดค่าพารามิเตอร์การเชื่อมต่ออนุกรม',
  '配置新的通信连接参数': 'กำหนดค่าพารามิเตอร์การเชื่อมต่อใหม่',
  '串口 (Serial)': 'อนุกรม (Serial)',
  'TCP / 网络': 'TCP / เครือข่าย',
  '基本信息': 'ข้อมูลพื้นฐาน',
  '通道名称': 'ชื่อช่องทาง',
  '例如：传感器A接口': 'ตัวอย่าง: อินเทอร์เฟซเซ็นเซอร์ A',
  '串口端口': 'พอร์ตอนุกรม',
  '选择串口': 'เลือกพอร์ตอนุกรม',
  '无可用串口': 'ไม่มีพอร์ตอนุกรมที่ใช้ได้',
  '目标地址': 'ที่อยู่เป้าหมาย',
  '例如：192.168.1.10': 'ตัวอย่าง: 192.168.1.10',
  '串口参数': 'พารามิเตอร์อนุกรม',
  '波特率': 'อัตรา baud',
  '数据位': 'บิตข้อมูล',
  '停止位': 'บิตหยุด',
  '校验位': 'พาริตี้',
  '无校验': 'ไม่มีพาริตี้',
  '奇校验': 'พาริตี้คี่',
  '偶校验': 'พาริตี้คู่',
  '流控': 'การควบคุมโฟลว์',
  '无': 'ไม่มี',
  '读超时 (ms)': 'หมดเวลาอ่าน (ms)',
  '写超时 (ms)': 'หมดเวลาเขียน (ms)',
  'TCP 端口': 'พอร์ต TCP',
  '保存后立即连接': 'เชื่อมต่อหลังบันทึก',
  '创建后立即启动连接': 'เริ่มเชื่อมต่อหลังสร้าง',
  '取消': 'ยกเลิก',
  '保存配置': 'บันทึกการกำหนดค่า',
  '创建通道': 'สร้างช่องทาง',
  '新建协议': 'โปรโตคอลใหม่',
  '配置协议': 'กำหนดค่าโปรโตคอล',
  '协议详情': 'รายละเอียดโปรโตคอล',
  '添加自定义协议元数据，供解析引擎识别。': 'เพิ่มเมตาดาตาโปรโตคอลกำหนดเองให้เครื่องมือแยกวิเคราะห์รู้จัก',
  '查看或更新协议描述与分类。': 'ดูหรืออัปเดตคำอธิบายและหมวดหมู่โปรโตคอล',
  '协议名称': 'ชื่อโปรโตคอล',
  '状态': 'สถานะ',
  '描述': 'คำอธิบาย',
  '驱动类': 'คลาสไดรเวอร์',
  '保存': 'บันทึก',
  '删除协议': 'ลบโปรโตคอล',
  '确认删除自定义协议': 'ยืนยันการลบโปรโตคอลกำหนดเอง',
  '吗？': '?',
  '确认删除': 'ยืนยันการลบ',
  'UI YAML 预览': 'ตัวอย่าง UI YAML',
  '脚本运行中展示 UI 渲染结果': 'แสดงผลการเรนเดอร์ UI ขณะสคริปต์ทำงาน',
  '解析失败': 'การแยกวิเคราะห์ล้มเหลว',
  '暂无可渲染的 UI 配置': 'ไม่มีการกำหนดค่า UI ที่เรนเดอร์ได้',
}
const viVN = {
  ...enUS,
  'nav.manual': 'Terminal nối tiếp',
  'nav.scripts': 'Script tự động hóa',
  'nav.proxy': 'Giám sát proxy',
  'nav.protocols': 'Trình quản lý giao thức',
  'nav.settings': 'Cài đặt',
  'nav.workspace': 'Không gian làm việc quản trị',
  'status.connected': 'Đã kết nối',
  'status.connecting': 'Đang kết nối',
  'status.error': 'Lỗi',
  'status.disconnected': 'Đã ngắt kết nối',
  'theme.system': 'Hệ thống',
  'theme.dark': 'Tối (Kỹ sư)',
  'theme.light': 'Sáng',
  'header.protocols.title': 'Trình quản lý giao thức',
  'header.protocols.desc': 'Định nghĩa giao thức, liên kết kênh và cấu hình quy tắc phân tích.',
  'action.refresh': 'Làm mới',
  'action.createProtocol': 'Giao thức mới',
  'protocol.tab.all': 'Tất cả giao thức',
  'protocol.tab.custom': 'Tùy chỉnh',
  'header.settings.title': 'Cài đặt ứng dụng',
  'header.settings.desc': 'Quản lý tùy chọn toàn cục, giá trị mặc định và cấu hình thời gian chạy.',
  'action.discardChanges': 'Hủy thay đổi',
  'action.saveChanges': 'Lưu thay đổi',
  'settings.tab.general': 'Chung',
  'settings.tab.plugins': 'Plugin',
  'settings.tab.runtime': 'Runtime',
  'settings.tab.logs': 'Nhật ký',
  'settings.language': 'Ngôn ngữ',
  'settings.theme': 'Chủ đề',
  'settings.autoConnect.title': 'Tự động kết nối khi khởi động',
  'settings.autoConnect.desc': 'Tự động kết nối lại kênh hoạt động gần nhất.',
  'settings.workspace': 'Không gian làm việc',
  'settings.chooseFolder': 'Chọn thư mục',
  'settings.plugins.title': 'Plugin',
  'settings.plugins.refresh': 'Làm mới danh sách',
  '空闲': 'Nhàn rỗi',
  '串口通道': 'Kênh nối tiếp',
  'TCP 客户端': 'Máy khách TCP',
  'TCP 服务端': 'Máy chủ TCP',
  '端口': 'Cổng',
  '运行中': 'Đang chạy',
  '请输入指令名称和内容': 'Nhập tên và nội dung lệnh',
  '协议': 'Giao thức',
  '可用': 'Có sẵn',
  '自定义': 'Tùy chỉnh',
  '已禁用': 'Vô hiệu hóa',
  '未知': 'Không xác định',
  '键名': 'Khóa',
  '驱动': 'Trình điều khiển',
  '分类': 'Danh mục',
  '搜索关键词': 'Tìm từ khóa',
  '选择工作区': 'Chọn không gian làm việc',
  '暂无描述': 'Không có mô tả',
  '配置': 'Cấu hình',
  '查看': 'Xem',
  '暂无协议': 'Không có giao thức',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Không có giao thức nào. Tạo từ mẫu tích hợp hoặc thêm tùy chỉnh.',
  'v1.2.4 - 已启用': 'v1.2.4 - Đã bật',
  '已启用': 'Đã bật',
  'MQTT 适配器': 'Bộ chuyển đổi MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - Chưa cài đặt',
  '未安装': 'Chưa cài đặt',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Không có mục nào có thể cấu hình. Cài đặt runtime sẽ mở khi mô-đun mở rộng.',
  '日志采集与归档策略将在后续版本中提供。': 'Chính sách thu thập và lưu trữ nhật ký sẽ có trong phiên bản tương lai.',
  '串口配置': 'Cấu hình nối tiếp',
  '新建通道': 'Kênh mới',
  '配置串口连接参数': 'Cấu hình tham số kết nối nối tiếp',
  '配置新的通信连接参数': 'Cấu hình tham số kết nối mới',
  '串口 (Serial)': 'Nối tiếp (Serial)',
  'TCP / 网络': 'TCP / Mạng',
  '基本信息': 'Thông tin cơ bản',
  '通道名称': 'Tên kênh',
  '例如：传感器A接口': 'Ví dụ: giao diện cảm biến A',
  '串口端口': 'Cổng nối tiếp',
  '选择串口': 'Chọn cổng nối tiếp',
  '无可用串口': 'Không có cổng nối tiếp khả dụng',
  '目标地址': 'Địa chỉ đích',
  '例如：192.168.1.10': 'Ví dụ: 192.168.1.10',
  '串口参数': 'Tham số nối tiếp',
  '波特率': 'Tốc độ baud',
  '数据位': 'Bit dữ liệu',
  '停止位': 'Bit dừng',
  '校验位': 'Chẵn lẻ',
  '无校验': 'Không chẵn lẻ',
  '奇校验': 'Chẵn lẻ lẻ',
  '偶校验': 'Chẵn lẻ chẵn',
  '流控': 'Điều khiển luồng',
  '无': 'Không',
  '读超时 (ms)': 'Hết thời gian đọc (ms)',
  '写超时 (ms)': 'Hết thời gian ghi (ms)',
  'TCP 端口': 'Cổng TCP',
  '保存后立即连接': 'Kết nối sau khi lưu',
  '创建后立即启动连接': 'Bắt đầu kết nối sau khi tạo',
  '取消': 'Hủy',
  '保存配置': 'Lưu cấu hình',
  '创建通道': 'Tạo kênh',
  '新建协议': 'Giao thức mới',
  '配置协议': 'Cấu hình giao thức',
  '协议详情': 'Chi tiết giao thức',
  '添加自定义协议元数据，供解析引擎识别。': 'Thêm siêu dữ liệu giao thức tùy chỉnh để bộ phân tích nhận diện.',
  '查看或更新协议描述与分类。': 'Xem hoặc cập nhật mô tả và danh mục giao thức.',
  '协议名称': 'Tên giao thức',
  '状态': 'Trạng thái',
  '描述': 'Mô tả',
  '驱动类': 'Lớp trình điều khiển',
  '保存': 'Lưu',
  '删除协议': 'Xóa giao thức',
  '确认删除自定义协议': 'Xác nhận xóa giao thức tùy chỉnh',
  '吗？': '?',
  '确认删除': 'Xác nhận xóa',
  'UI YAML 预览': 'Xem trước UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Hiển thị kết quả render UI khi script chạy',
  '解析失败': 'Phân tích thất bại',
  '暂无可渲染的 UI 配置': 'Không có cấu hình UI có thể render',
}
const idID = {
  ...enUS,
  'nav.manual': 'Terminal serial',
  'nav.scripts': 'Skrip otomatisasi',
  'nav.proxy': 'Monitor proxy',
  'nav.protocols': 'Manajer protokol',
  'nav.settings': 'Pengaturan',
  'nav.workspace': 'Ruang kerja admin',
  'status.connected': 'Terhubung',
  'status.connecting': 'Menghubungkan',
  'status.error': 'Kesalahan',
  'status.disconnected': 'Terputus',
  'theme.system': 'Sistem',
  'theme.dark': 'Gelap (Insinyur)',
  'theme.light': 'Terang',
  'header.protocols.title': 'Manajer protokol',
  'header.protocols.desc': 'Tentukan protokol, kaitkan kanal, dan konfigurasi aturan parsing.',
  'action.refresh': 'Muat ulang',
  'action.createProtocol': 'Protokol baru',
  'protocol.tab.all': 'Semua protokol',
  'protocol.tab.custom': 'Kustom',
  'header.settings.title': 'Pengaturan aplikasi',
  'header.settings.desc': 'Kelola preferensi global, nilai default, dan konfigurasi runtime.',
  'action.discardChanges': 'Batalkan perubahan',
  'action.saveChanges': 'Simpan perubahan',
  'settings.tab.general': 'Umum',
  'settings.tab.plugins': 'Plugin',
  'settings.tab.runtime': 'Runtime',
  'settings.tab.logs': 'Log',
  'settings.language': 'Bahasa',
  'settings.theme': 'Tema',
  'settings.autoConnect.title': 'Sambung otomatis saat mulai',
  'settings.autoConnect.desc': 'Sambungkan kembali ke kanal aktif terakhir secara otomatis.',
  'settings.workspace': 'Ruang kerja',
  'settings.chooseFolder': 'Pilih folder',
  'settings.plugins.title': 'Plugin',
  'settings.plugins.refresh': 'Muat ulang daftar',
  '空闲': 'Menganggur',
  '串口通道': 'Kanal serial',
  'TCP 客户端': 'Klien TCP',
  'TCP 服务端': 'Server TCP',
  '端口': 'Port',
  '运行中': 'Berjalan',
  '请输入指令名称和内容': 'Masukkan nama dan isi perintah',
  '协议': 'Protokol',
  '可用': 'Tersedia',
  '自定义': 'Kustom',
  '已禁用': 'Dinonaktifkan',
  '未知': 'Tidak diketahui',
  '键名': 'Kunci',
  '驱动': 'Driver',
  '分类': 'Kategori',
  '搜索关键词': 'Cari kata kunci',
  '选择工作区': 'Pilih ruang kerja',
  '暂无描述': 'Tidak ada deskripsi',
  '配置': 'Konfigurasi',
  '查看': 'Lihat',
  '暂无协议': 'Tidak ada protokol',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Tidak ada protokol tersedia. Buat dari template bawaan atau tambah kustom.',
  'v1.2.4 - 已启用': 'v1.2.4 - Diaktifkan',
  '已启用': 'Diaktifkan',
  'MQTT 适配器': 'Adaptor MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - Belum terpasang',
  '未安装': 'Belum terpasang',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Tidak ada item yang dapat dikonfigurasi. Pengaturan runtime akan tersedia saat modul diperluas.',
  '日志采集与归档策略将在后续版本中提供。': 'Kebijakan pengumpulan dan pengarsipan log akan tersedia pada rilis mendatang.',
  '串口配置': 'Konfigurasi serial',
  '新建通道': 'Kanal baru',
  '配置串口连接参数': 'Konfigurasi parameter koneksi serial',
  '配置新的通信连接参数': 'Konfigurasi parameter koneksi baru',
  '串口 (Serial)': 'Serial (Serial)',
  'TCP / 网络': 'TCP / Jaringan',
  '基本信息': 'Info dasar',
  '通道名称': 'Nama kanal',
  '例如：传感器A接口': 'Contoh: antarmuka sensor A',
  '串口端口': 'Port serial',
  '选择串口': 'Pilih port serial',
  '无可用串口': 'Tidak ada port serial yang tersedia',
  '目标地址': 'Alamat target',
  '例如：192.168.1.10': 'Contoh: 192.168.1.10',
  '串口参数': 'Parameter serial',
  '波特率': 'Laju baud',
  '数据位': 'Bit data',
  '停止位': 'Bit stop',
  '校验位': 'Paritas',
  '无校验': 'Tanpa paritas',
  '奇校验': 'Paritas ganjil',
  '偶校验': 'Paritas genap',
  '流控': 'Kontrol aliran',
  '无': 'Tidak ada',
  '读超时 (ms)': 'Batas waktu baca (ms)',
  '写超时 (ms)': 'Batas waktu tulis (ms)',
  'TCP 端口': 'Port TCP',
  '保存后立即连接': 'Hubungkan setelah menyimpan',
  '创建后立即启动连接': 'Mulai koneksi setelah dibuat',
  '取消': 'Batal',
  '保存配置': 'Simpan konfigurasi',
  '创建通道': 'Buat kanal',
  '新建协议': 'Protokol baru',
  '配置协议': 'Konfigurasi protokol',
  '协议详情': 'Detail protokol',
  '添加自定义协议元数据，供解析引擎识别。': 'Tambahkan metadata protokol kustom agar mesin parser mengenalinya.',
  '查看或更新协议描述与分类。': 'Lihat atau perbarui deskripsi dan kategori protokol.',
  '协议名称': 'Nama protokol',
  '状态': 'Status',
  '描述': 'Deskripsi',
  '驱动类': 'Kelas driver',
  '保存': 'Simpan',
  '删除协议': 'Hapus protokol',
  '确认删除自定义协议': 'Konfirmasi hapus protokol kustom',
  '吗？': '?',
  '确认删除': 'Konfirmasi hapus',
  'UI YAML 预览': 'Pratinjau UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Tampilkan rendering UI saat skrip berjalan',
  '解析失败': 'Gagal parsing',
  '暂无可渲染的 UI 配置': 'Tidak ada konfigurasi UI yang dapat dirender',
}
const trTR = {
  ...enUS,
  'nav.manual': 'Seri terminal',
  'nav.scripts': 'Otomasyon betikleri',
  'nav.proxy': 'Proxy izleyici',
  'nav.protocols': 'Protokol yöneticisi',
  'nav.settings': 'Ayarlar',
  'nav.workspace': 'Yönetici çalışma alanı',
  'status.connected': 'Bağlı',
  'status.connecting': 'Bağlanıyor',
  'status.error': 'Hata',
  'status.disconnected': 'Bağlı değil',
  'theme.system': 'Sistem',
  'theme.dark': 'Koyu (Mühendis)',
  'theme.light': 'Açık',
  'header.protocols.title': 'Protokol yöneticisi',
  'header.protocols.desc': 'Protokolleri tanımlayın, kanalları bağlayın ve ayrıştırma kurallarını yapılandırın.',
  'action.refresh': 'Yenile',
  'action.createProtocol': 'Yeni protokol',
  'protocol.tab.all': 'Tüm protokoller',
  'protocol.tab.custom': 'Özel',
  'header.settings.title': 'Uygulama ayarları',
  'header.settings.desc': 'Genel tercihleri, varsayılanları ve çalışma zamanı yapılandırmasını yönetin.',
  'action.discardChanges': 'Değişiklikleri at',
  'action.saveChanges': 'Değişiklikleri kaydet',
  'settings.tab.general': 'Genel',
  'settings.tab.plugins': 'Eklentiler',
  'settings.tab.runtime': 'Çalışma zamanı',
  'settings.tab.logs': 'Günlükler',
  'settings.language': 'Dil',
  'settings.theme': 'Tema',
  'settings.autoConnect.title': 'Başlangıçta otomatik bağlan',
  'settings.autoConnect.desc': 'Son etkin kanala otomatik olarak yeniden bağlan.',
  'settings.workspace': 'Çalışma alanı',
  'settings.chooseFolder': 'Klasör seç',
  'settings.plugins.title': 'Eklentiler',
  'settings.plugins.refresh': 'Listeyi yenile',
  '空闲': 'Boşta',
  '串口通道': 'Seri kanal',
  'TCP 客户端': 'TCP istemcisi',
  'TCP 服务端': 'TCP sunucusu',
  '端口': 'Port',
  '运行中': 'Çalışıyor',
  '请输入指令名称和内容': 'Komut adı ve içeriğini girin',
  '协议': 'Protokol',
  '可用': 'Kullanılabilir',
  '自定义': 'Özel',
  '已禁用': 'Devre dışı',
  '未知': 'Bilinmeyen',
  '键名': 'Anahtar',
  '驱动': 'Sürücü',
  '分类': 'Kategori',
  '搜索关键词': 'Anahtar kelime ara',
  '选择工作区': 'Çalışma alanı seç',
  '暂无描述': 'Açıklama yok',
  '配置': 'Yapılandır',
  '查看': 'Görüntüle',
  '暂无协议': 'Protokol yok',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Kullanılabilir protokol yok. Dahili şablonlardan oluşturun veya özel ekleyin.',
  'v1.2.4 - 已启用': 'v1.2.4 - Etkin',
  '已启用': 'Etkin',
  'MQTT 适配器': 'MQTT adaptörü',
  'v0.9.8 - 未安装': 'v0.9.8 - Yüklü değil',
  '未安装': 'Yüklü değil',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Yapılandırılabilir öğe yok. Çalışma zamanı ayarları modüller genişledikçe açılacaktır.',
  '日志采集与归档策略将在后续版本中提供。': 'Günlük toplama ve arşivleme politikaları gelecekteki bir sürümde sunulacak.',
  '串口配置': 'Seri yapılandırma',
  '新建通道': 'Yeni kanal',
  '配置串口连接参数': 'Seri bağlantı parametrelerini yapılandır',
  '配置新的通信连接参数': 'Yeni bağlantı parametrelerini yapılandır',
  '串口 (Serial)': 'Seri (Serial)',
  'TCP / 网络': 'TCP / Ağ',
  '基本信息': 'Temel bilgiler',
  '通道名称': 'Kanal adı',
  '例如：传感器A接口': 'Örnek: Sensör A arayüzü',
  '串口端口': 'Seri port',
  '选择串口': 'Seri port seç',
  '无可用串口': 'Kullanılabilir seri port yok',
  '目标地址': 'Hedef adres',
  '例如：192.168.1.10': 'Örnek: 192.168.1.10',
  '串口参数': 'Seri parametreler',
  '波特率': 'Baud hızı',
  '数据位': 'Veri bitleri',
  '停止位': 'Stop bitleri',
  '校验位': 'Parite',
  '无校验': 'Parite yok',
  '奇校验': 'Tek parite',
  '偶校验': 'Çift parite',
  '流控': 'Akış kontrolü',
  '无': 'Yok',
  '读超时 (ms)': 'Okuma zaman aşımı (ms)',
  '写超时 (ms)': 'Yazma zaman aşımı (ms)',
  'TCP 端口': 'TCP portu',
  '保存后立即连接': 'Kaydettikten sonra bağlan',
  '创建后立即启动连接': 'Oluşturulduktan sonra bağlantıyı başlat',
  '取消': 'İptal',
  '保存配置': 'Yapılandırmayı kaydet',
  '创建通道': 'Kanal oluştur',
  '新建协议': 'Yeni protokol',
  '配置协议': 'Protokolü yapılandır',
  '协议详情': 'Protokol ayrıntıları',
  '添加自定义协议元数据，供解析引擎识别。': 'Çözümleyici motorun tanıması için özel protokol meta verileri ekle.',
  '查看或更新协议描述与分类。': 'Protokol açıklaması ve kategorisini görüntüleyin veya güncelleyin.',
  '协议名称': 'Protokol adı',
  '状态': 'Durum',
  '描述': 'Açıklama',
  '驱动类': 'Sürücü sınıfı',
  '保存': 'Kaydet',
  '删除协议': 'Protokolü sil',
  '确认删除自定义协议': 'Özel protokolü silmeyi onayla',
  '吗？': '?',
  '确认删除': 'Silmeyi onayla',
  'UI YAML 预览': 'UI YAML önizleme',
  '脚本运行中展示 UI 渲染结果': 'Betik çalışırken UI render sonucunu göster',
  '解析失败': 'Ayrıştırma başarısız',
  '暂无可渲染的 UI 配置': 'Render edilebilir UI yapılandırması yok',
}
const plPL = {
  ...enUS,
  'nav.manual': 'Terminal szeregowy',
  'nav.scripts': 'Skrypty automatyzacji',
  'nav.proxy': 'Monitor proxy',
  'nav.protocols': 'Menedżer protokołów',
  'nav.settings': 'Ustawienia',
  'nav.workspace': 'Obszar roboczy administratora',
  'status.connected': 'Połączono',
  'status.connecting': 'Łączenie',
  'status.error': 'Błąd',
  'status.disconnected': 'Rozłączono',
  'theme.system': 'System',
  'theme.dark': 'Ciemny (Inżynier)',
  'theme.light': 'Jasny',
  'header.protocols.title': 'Menedżer protokołów',
  'header.protocols.desc': 'Definiuj protokoły, przypisuj kanały i konfiguruj reguły parsowania.',
  'action.refresh': 'Odśwież',
  'action.createProtocol': 'Nowy protokół',
  'protocol.tab.all': 'Wszystkie protokoły',
  'protocol.tab.custom': 'Niestandardowy',
  'header.settings.title': 'Ustawienia aplikacji',
  'header.settings.desc': 'Zarządzaj globalnymi preferencjami, domyślnymi wartościami i konfiguracją uruchomieniową.',
  'action.discardChanges': 'Odrzuć zmiany',
  'action.saveChanges': 'Zapisz zmiany',
  'settings.tab.general': 'Ogólne',
  'settings.tab.plugins': 'Wtyczki',
  'settings.tab.runtime': 'Środowisko wykonawcze',
  'settings.tab.logs': 'Logi',
  'settings.language': 'Język',
  'settings.theme': 'Motyw',
  'settings.autoConnect.title': 'Automatyczne łączenie przy starcie',
  'settings.autoConnect.desc': 'Automatycznie łącz z ostatnim aktywnym kanałem.',
  'settings.workspace': 'Obszar roboczy',
  'settings.chooseFolder': 'Wybierz folder',
  'settings.plugins.title': 'Wtyczki',
  'settings.plugins.refresh': 'Odśwież listę',
  '空闲': 'Bezczynny',
  '串口通道': 'Kanał szeregowy',
  'TCP 客户端': 'Klient TCP',
  'TCP 服务端': 'Serwer TCP',
  '端口': 'Port',
  '运行中': 'Uruchomiony',
  '请输入指令名称和内容': 'Wprowadź nazwę i treść polecenia',
  '协议': 'Protokół',
  '可用': 'Dostępne',
  '自定义': 'Niestandardowy',
  '已禁用': 'Wyłączony',
  '未知': 'Nieznany',
  '键名': 'Klucz',
  '驱动': 'Sterownik',
  '分类': 'Kategoria',
  '搜索关键词': 'Szukaj słów kluczowych',
  '选择工作区': 'Wybierz obszar roboczy',
  '暂无描述': 'Brak opisu',
  '配置': 'Konfiguruj',
  '查看': 'Wyświetl',
  '暂无协议': 'Brak protokołów',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Brak dostępnych protokołów. Utwórz z wbudowanych szablonów lub dodaj niestandardowy.',
  'v1.2.4 - 已启用': 'v1.2.4 - Włączony',
  '已启用': 'Włączony',
  'MQTT 适配器': 'Adapter MQTT',
  'v0.9.8 - 未安装': 'v0.9.8 - Nie zainstalowano',
  '未安装': 'Nie zainstalowano',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Brak konfigurowalnych elementów. Ustawienia uruchomieniowe będą dostępne wraz z rozbudową modułów.',
  '日志采集与归档策略将在后续版本中提供。': 'Zasady zbierania i archiwizacji logów będą dostępne w przyszłej wersji.',
  '串口配置': 'Konfiguracja szeregowa',
  '新建通道': 'Nowy kanał',
  '配置串口连接参数': 'Skonfiguruj parametry połączenia szeregowego',
  '配置新的通信连接参数': 'Skonfiguruj nowe parametry połączenia',
  '串口 (Serial)': 'Szeregowy (Serial)',
  'TCP / 网络': 'TCP / Sieć',
  '基本信息': 'Podstawowe informacje',
  '通道名称': 'Nazwa kanału',
  '例如：传感器A接口': 'Przykład: interfejs czujnika A',
  '串口端口': 'Port szeregowy',
  '选择串口': 'Wybierz port szeregowy',
  '无可用串口': 'Brak dostępnych portów szeregowych',
  '目标地址': 'Adres docelowy',
  '例如：192.168.1.10': 'Przykład: 192.168.1.10',
  '串口参数': 'Parametry szeregowe',
  '波特率': 'Prędkość baud',
  '数据位': 'Bity danych',
  '停止位': 'Bity stopu',
  '校验位': 'Parzystość',
  '无校验': 'Brak parzystości',
  '奇校验': 'Parzystość nieparzysta',
  '偶校验': 'Parzystość parzysta',
  '流控': 'Kontrola przepływu',
  '无': 'Brak',
  '读超时 (ms)': 'Limit czasu odczytu (ms)',
  '写超时 (ms)': 'Limit czasu zapisu (ms)',
  'TCP 端口': 'Port TCP',
  '保存后立即连接': 'Połącz po zapisaniu',
  '创建后立即启动连接': 'Uruchom połączenie po utworzeniu',
  '取消': 'Anuluj',
  '保存配置': 'Zapisz konfigurację',
  '创建通道': 'Utwórz kanał',
  '新建协议': 'Nowy protokół',
  '配置协议': 'Konfiguruj protokół',
  '协议详情': 'Szczegóły protokołu',
  '添加自定义协议元数据，供解析引擎识别。': 'Dodaj niestandardowe metadane protokołu, aby silnik parsera je rozpoznał.',
  '查看或更新协议描述与分类。': 'Wyświetl lub zaktualizuj opis i kategorię protokołu.',
  '协议名称': 'Nazwa protokołu',
  '状态': 'Status',
  '描述': 'Opis',
  '驱动类': 'Klasa sterownika',
  '保存': 'Zapisz',
  '删除协议': 'Usuń protokół',
  '确认删除自定义协议': 'Potwierdź usunięcie niestandardowego protokołu',
  '吗？': '?',
  '确认删除': 'Potwierdź usunięcie',
  'UI YAML 预览': 'Podgląd UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Pokaż renderowanie UI podczas działania skryptu',
  '解析失败': 'Nieudane parsowanie',
  '暂无可渲染的 UI 配置': 'Brak renderowalnej konfiguracji UI',
}
const ukUA = {
  ...enUS,
  'nav.manual': 'Послідовний термінал',
  'nav.scripts': 'Скрипти автоматизації',
  'nav.proxy': 'Монітор проксі',
  'nav.protocols': 'Менеджер протоколів',
  'nav.settings': 'Налаштування',
  'nav.workspace': 'Робочий простір адміністратора',
  'status.connected': 'Підключено',
  'status.connecting': 'Підключення',
  'status.error': 'Помилка',
  'status.disconnected': 'Відключено',
  'theme.system': 'Система',
  'theme.dark': 'Темна (Інженер)',
  'theme.light': 'Світла',
  'header.protocols.title': 'Менеджер протоколів',
  'header.protocols.desc': 'Визначайте протоколи, прив’язуйте канали та налаштовуйте правила розбору.',
  'action.refresh': 'Оновити',
  'action.createProtocol': 'Новий протокол',
  'protocol.tab.all': 'Усі протоколи',
  'protocol.tab.custom': 'Користувацький',
  'header.settings.title': 'Налаштування застосунку',
  'header.settings.desc': 'Керуйте глобальними параметрами, значеннями за замовчуванням і конфігурацією виконання.',
  'action.discardChanges': 'Скасувати зміни',
  'action.saveChanges': 'Зберегти зміни',
  'settings.tab.general': 'Загальні',
  'settings.tab.plugins': 'Плагіни',
  'settings.tab.runtime': 'Виконання',
  'settings.tab.logs': 'Журнали',
  'settings.language': 'Мова',
  'settings.theme': 'Тема',
  'settings.autoConnect.title': 'Автопідключення під час запуску',
  'settings.autoConnect.desc': 'Автоматично перепідключатися до останнього активного каналу.',
  'settings.workspace': 'Робочий простір',
  'settings.chooseFolder': 'Вибрати папку',
  'settings.plugins.title': 'Плагіни',
  'settings.plugins.refresh': 'Оновити список',
  '空闲': 'Бездіяльний',
  '串口通道': 'Послідовний канал',
  'TCP 客户端': 'TCP-клієнт',
  'TCP 服务端': 'TCP-сервер',
  '端口': 'Порт',
  '运行中': 'Працює',
  '请输入指令名称和内容': 'Введіть назву та вміст команди',
  '协议': 'Протокол',
  '可用': 'Доступний',
  '自定义': 'Користувацький',
  '已禁用': 'Вимкнений',
  '未知': 'Невідомо',
  '键名': 'Ключ',
  '驱动': 'Драйвер',
  '分类': 'Категорія',
  '搜索关键词': 'Пошук ключових слів',
  '选择工作区': 'Вибрати робочий простір',
  '暂无描述': 'Без опису',
  '配置': 'Налаштувати',
  '查看': 'Переглянути',
  '暂无协议': 'Немає протоколів',
  '暂无可用协议，可从内置模板创建或新增自定义协议。': 'Немає доступних протоколів. Створіть із вбудованих шаблонів або додайте власний.',
  'v1.2.4 - 已启用': 'v1.2.4 - Увімкнено',
  '已启用': 'Увімкнено',
  'MQTT 适配器': 'MQTT-адаптер',
  'v0.9.8 - 未安装': 'v0.9.8 - Не встановлено',
  '未安装': 'Не встановлено',
  '暂无可配置项，运行时设置将随着模块扩展开放。': 'Немає елементів для налаштування. Налаштування виконання будуть доступні зі зростанням модулів.',
  '日志采集与归档策略将在后续版本中提供。': 'Політики збору та архівації журналів будуть доступні у майбутньому випуску.',
  '串口配置': 'Послідовна конфігурація',
  '新建通道': 'Новий канал',
  '配置串口连接参数': 'Налаштувати параметри послідовного з’єднання',
  '配置新的通信连接参数': 'Налаштувати нові параметри з’єднання',
  '串口 (Serial)': 'Послідовний (Serial)',
  'TCP / 网络': 'TCP / Мережа',
  '基本信息': 'Основна інформація',
  '通道名称': 'Назва каналу',
  '例如：传感器A接口': 'Приклад: інтерфейс датчика A',
  '串口端口': 'Послідовний порт',
  '选择串口': 'Вибрати послідовний порт',
  '无可用串口': 'Немає доступних послідовних портів',
  '目标地址': 'Цільова адреса',
  '例如：192.168.1.10': 'Приклад: 192.168.1.10',
  '串口参数': 'Параметри послідовного порту',
  '波特率': 'Швидкість бод',
  '数据位': 'Біти даних',
  '停止位': 'Стоп-біти',
  '校验位': 'Парність',
  '无校验': 'Без парності',
  '奇校验': 'Непарна парність',
  '偶校验': 'Парна парність',
  '流控': 'Керування потоком',
  '无': 'Немає',
  '读超时 (ms)': 'Тайм-аут читання (мс)',
  '写超时 (ms)': 'Тайм-аут запису (мс)',
  'TCP 端口': 'TCP-порт',
  '保存后立即连接': 'Підключити після збереження',
  '创建后立即启动连接': 'Запустити підключення після створення',
  '取消': 'Скасувати',
  '保存配置': 'Зберегти конфігурацію',
  '创建通道': 'Створити канал',
  '新建协议': 'Новий протокол',
  '配置协议': 'Налаштувати протокол',
  '协议详情': 'Деталі протоколу',
  '添加自定义协议元数据，供解析引擎识别。': 'Додайте користувацькі метадані протоколу, щоб рушій аналізу їх розпізнав.',
  '查看或更新协议描述与分类。': 'Переглянути або оновити опис і категорію протоколу.',
  '协议名称': 'Назва протоколу',
  '状态': 'Статус',
  '描述': 'Опис',
  '驱动类': 'Клас драйвера',
  '保存': 'Зберегти',
  '删除协议': 'Видалити протокол',
  '确认删除自定义协议': 'Підтвердити видалення користувацького протоколу',
  '吗？': '?',
  '确认删除': 'Підтвердити видалення',
  'UI YAML 预览': 'Попередній перегляд UI YAML',
  '脚本运行中展示 UI 渲染结果': 'Показувати рендеринг UI під час виконання скрипту',
  '解析失败': 'Помилка розбору',
  '暂无可渲染的 UI 配置': 'Немає конфігурації UI для рендерингу',
}

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

const supportedLanguages = new Set([
  'zh-CN',
  'zh-TW',
  'en-US',
  'ja-JP',
  'ko-KR',
  'fr-FR',
  'de-DE',
  'es-ES',
  'pt-BR',
  'ru-RU',
  'ar',
  'hi',
  'it-IT',
  'nl-NL',
  'th-TH',
  'vi-VN',
  'id-ID',
  'tr-TR',
  'pl-PL',
  'uk-UA',
])

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
  let normalized = map[lowered] || ''
  if (!normalized) {
    if (raw === '简体中文') normalized = 'zh-CN'
    else if (raw === '繁體中文' || raw === '繁体中文') normalized = 'zh-TW'
    else if (raw === 'English (US)') normalized = 'en-US'
  }
  if (!normalized) return 'zh-CN'
  return supportedLanguages.has(normalized) ? normalized : 'zh-CN'
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


