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
import ChannelDialogModal from './components/ChannelDialogModal.vue'
import SettingsPanels from './components/SettingsPanels.vue'
import SettingsHeader from './components/SettingsHeader.vue'
import ProtocolCardsSection from './components/ProtocolCardsSection.vue'
import ProtocolHeader from './components/ProtocolHeader.vue'
import ProtocolEditModal from './components/ProtocolEditModal.vue'
import ProtocolDeleteModal from './components/ProtocolDeleteModal.vue'
import UiYamlPreviewModal from './components/UiYamlPreviewModal.vue'
import { yaml as yamlLanguage } from '@codemirror/lang-yaml'
import { useUiRuntimeStore } from './stores/uiRuntime'
import * as i18nCore from './i18n'
import { fallbackPorts, networkDefaults, serialDefaults, supportedBaudRates, uiDefaults } from './config/runtimeDefaults'
import { normalizeSerialPortName } from './utils/serialPort'
import { useChannelState } from './composables/useChannelState'
import { useSerialInteraction } from './composables/useSerialInteraction'
import { useChannelDialog } from './composables/useChannelDialog'
import { usePayloadSender } from './composables/usePayloadSender'
import { useYamlDocumentOps } from './composables/useYamlDocumentOps'
import { useScriptRunner } from './composables/useScriptRunner'
import { useScriptLogHelpers } from './composables/useScriptLogHelpers'
import { useYamlSearch } from './composables/useYamlSearch'
import { useScriptBridgeSignals } from './composables/useScriptBridgeSignals'
import { useCommBridgeSignals } from './composables/useCommBridgeSignals'
import { useSettingsState } from './composables/useSettingsState'
import { useSettingsPersistence } from './composables/useSettingsPersistence'
import { useSettingsBridge } from './composables/useSettingsBridge'
import { useProtocolManager } from './composables/useProtocolManager'

const bridge = ref(null)
const sidebarRef = ref(null)
const connectionInfo = ref({ state: 'disconnected', detail: '' })
const ports = ref([])
const selectedPort = ref('')
const baud = ref(serialDefaults.baud)
const tcpHost = ref(networkDefaults.host)
const tcpPort = ref(networkDefaults.port)
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
const portPlaceholder = serialDefaults.portPlaceholder
const channelDialogOpen = ref(false)
const channelDialogMode = ref('create')
const channelType = ref('serial')
const channelName = ref('')
const channelPort = ref('')
const channelBaud = ref(serialDefaults.baud)
const channelDataBits = ref(serialDefaults.dataBits)
const channelParity = ref(serialDefaults.parity)
const channelStopBits = ref(serialDefaults.stopBits)
const channelFlowControl = ref(serialDefaults.flowControl)
const channelReadTimeout = ref(serialDefaults.readTimeoutMs)
const channelWriteTimeout = ref(serialDefaults.writeTimeoutMs)
const channelHost = ref(networkDefaults.host)
const channelTcpPort = ref(networkDefaults.port)
const channelAutoConnect = ref(true)
const uiLanguage = ref(uiDefaults.language)
const uiTheme = ref(uiDefaults.theme)
const defaultBaud = ref(serialDefaults.baud)
const defaultParity = ref(serialDefaults.parity)
const defaultStopBits = ref(serialDefaults.stopBits)
const tcpTimeoutMs = ref(networkDefaults.timeoutMs)
const tcpHeartbeatSec = ref(networkDefaults.heartbeatSec)
const tcpRetryCount = ref(networkDefaults.retryCount)
const dslWorkspacePath = ref('/usr/local/protoflow/workflows')
const autoConnectOnStart = ref(uiDefaults.autoConnectOnStart)
const settingsSaving = ref(false)
const settingsSnapshot = ref(null)
const settingsTab = ref('general')
const { translations, supportedLanguages, DEFAULT_LANGUAGE } = i18nCore

const t = (key, fallback = '') => {
  const lang = uiLanguage.value || DEFAULT_LANGUAGE
  return translations[lang]?.[key] ?? translations[DEFAULT_LANGUAGE]?.[key] ?? fallback ?? key
}

const tr = (text) => {
  const lang = uiLanguage.value || DEFAULT_LANGUAGE
  const key = String(text ?? '')
  return translations[lang]?.[key] ?? translations[DEFAULT_LANGUAGE]?.[key] ?? key
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
const uiRuntime = useUiRuntimeStore()
const uiModalOpen = ref(false)
const appVersion = ref('')
const { noPorts, portOptionsList, applyPorts, selectPort: selectChannelPort } = useChannelState(ports, selectedPort)
const { resolveSerialPort } = useSerialInteraction()

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
const appVersionLabel = computed(() => appVersion.value || uiDefaults.appVersionFallback)

const filteredChannelCards = computed(() => {
  if (channelTab.value === 'all') return channelCards.value
  return channelCards.value.filter((card) => card.category === channelTab.value)
})

const {
  protocolTab,
  protocolDialogOpen,
  protocolDialogMode,
  protocolEditing,
  protocolDeleteOpen,
  protocolDeleting,
  protocolDraft,
  filteredProtocolCards,
  refreshProtocols,
  openCreateProtocol,
  openProtocolDetails,
  closeProtocolDialog,
  updateProtocolDraft,
  saveProtocol,
  openProtocolDelete,
  closeProtocolDelete,
  confirmProtocolDelete,
  setProtocolTab,
} = useProtocolManager({
  bridge,
  tr,
  withResult,
})

const { handleNewChannel, openChannelSettings, closeChannelDialog, submitChannelDialog } = useChannelDialog({
  refs: {
    channelDialogOpen,
    channelDialogMode,
    channelType,
    channelName,
    channelPort,
    channelBaud,
    channelDataBits,
    channelParity,
    channelStopBits,
    channelFlowControl,
    channelReadTimeout,
    channelWriteTimeout,
    channelHost,
    channelTcpPort,
    channelAutoConnect,
    selectedPort,
    ports,
    defaultBaud,
    defaultParity,
    defaultStopBits,
    tcpHost,
    tcpPort,
    autoConnectOnStart,
  },
  defaults: {
    fallbackPorts,
    serialDefaults: { baud: serialDefaults.baud },
    networkDefaults: { host: networkDefaults.host },
  },
  bridge,
  normalizeSerialPortName,
})

const { sendPayload, sendQuickCommand } = usePayloadSender({
  bridge,
  sendMode,
  sendText,
  sendHex,
  appendCR,
  appendLF,
})

const { loadYaml, saveYaml, handleYamlFile, copyYaml } = useYamlDocumentOps({
  bridge,
  withResult,
  yamlText,
  scriptFileName,
  scriptFilePath,
  yamlFileInputRef,
  refreshScriptVariables,
  addScriptLog,
})

const { openUiYamlModal, closeUiYamlModal, runScript, stopScript } = useScriptRunner({
  bridge,
  uiRuntime,
  uiModalOpen,
  yamlText,
  scriptRunning,
  scriptState,
  scriptStartMs,
  scriptElapsedMs,
  scriptProgress,
  addScriptLog,
})

const { searchYaml } = useYamlSearch({
  tr,
  addScriptLog,
  getEditor: () => yamlEditor,
})

const { clearScriptLogs, scrollScriptLogsToBottom, refreshScriptVariables } = useScriptLogHelpers({
  scriptLogs,
  scriptLogBuffer,
  scriptLogRef,
  scriptVariablesList,
  yamlText,
  parseScriptVariables,
  clearScriptVarTimer: () => {
    if (scriptVarTimer) {
      window.clearTimeout(scriptVarTimer)
      scriptVarTimer = null
    }
  },
})

const { bindScriptBridgeSignals } = useScriptBridgeSignals({
  scriptRunning,
  scriptState,
  scriptProgress,
  addScriptLog,
  scheduleSetChannels,
})

const { bindCommBridgeSignals } = useCommBridgeSignals({
  parseBridgePayload,
  addCommLog,
  addCommBatch,
  ingestCaptureFrame,
  emitStatus,
  scheduleChannelRefresh,
  setConnectingFalse: () => {
    isConnecting.value = false
  },
  onConnectionInfo: (nextInfo) => {
    connectionInfo.value = nextInfo
  },
  shouldEmitDisconnected: (reason) => hasStatusActivity || Boolean(reason),
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
let channelUpdateRaf = 0
let pendingChannelItems = null
let scriptLogScrollRaf = 0
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
  const hasErrors = Array.isArray(payload.errors) && payload.errors.length > 0
  const direction = payload.direction || 'RX'
  const tone = unknown || hasErrors ? 'red' : direction === 'TX' ? 'blue' : 'green'
  return {
    id: payload.id || `cap-${Date.now()}`,
    direction,
    time: formatCaptureTime(payload.timestamp || Date.now() / 1000),
    size: payload.length || 0,
    note: payload.raw_hex || '',
    summary: payload.summary || '',
    summaryText: payload.summary || '',
    tone,
    warn: unknown || hasErrors,
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
    applyPorts(items)
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

function scheduleSetChannels(items) {
  pendingChannelItems = items
  if (channelUpdateRaf) return
  channelUpdateRaf = window.requestAnimationFrame(() => {
    channelUpdateRaf = 0
    const next = pendingChannelItems
    pendingChannelItems = null
    setChannels(next)
  })
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

function handleChannelRefresh() {
  refreshChannels()
  refreshPorts()
}

function connectSerial() {
  if (!bridge.value) return
  if (isConnecting.value || isConnected.value) return
  const targetPort = resolveSerialPort(selectedPort.value)
  if (!targetPort) return
  selectedPort.value = targetPort
  isConnecting.value = true
  bridge.value.connect_serial(targetPort, Number(baud.value))
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
  bindCommBridgeSignals(obj)
  bindScriptBridgeSignals(obj)
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
  if (channelUpdateRaf) {
    window.cancelAnimationFrame(channelUpdateRaf)
    channelUpdateRaf = 0
  }
  if (scriptLogScrollRaf) {
    window.cancelAnimationFrame(scriptLogScrollRaf)
    scriptLogScrollRaf = 0
  }
  destroyYamlEditor()
  window.removeEventListener('keydown', handleGlobalKeydown)
})

watch(
  () => scriptLogs.value.length,
  () => {
    if (!scriptAutoScroll.value) return
    if (scriptLogScrollRaf) return
    scriptLogScrollRaf = window.requestAnimationFrame(async () => {
      scriptLogScrollRaf = 0
      await nextTick()
      scrollScriptLogsToBottom()
    })
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
  if (!item) return
  selectChannelPort(item)
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

const { buildSettingsPayload, normalizeSettings, applySettings } = useSettingsPersistence({
  refs: {
    uiLanguage,
    uiTheme,
    autoConnectOnStart,
    dslWorkspacePath,
    quickCommands,
    defaultBaud,
    defaultParity,
    defaultStopBits,
    tcpTimeoutMs,
    tcpHeartbeatSec,
    tcpRetryCount,
    baud,
  },
  defaults: {
    uiDefaults,
    serialDefaults,
    networkDefaults,
    defaultLanguage: DEFAULT_LANGUAGE,
    supportedLanguages,
    workspaceFallback: '/usr/local/protoflow/workflows',
  },
  normalizeQuickCommands,
})

const {
  settingsDirty,
  setSnapshot: setSettingsSnapshot,
  commitCurrent: commitSettingsSnapshot,
  discard: discardSettings,
} = useSettingsState({
  settingsSnapshot,
  buildPayload: buildSettingsPayload,
  normalize: normalizeSettings,
  apply: applySettings,
})

const { loadSettings, saveSettings, chooseDslWorkspace } = useSettingsBridge({
  bridge,
  settingsSaving,
  dslWorkspacePath,
  tr,
  withResult,
  normalizeSettings,
  applySettings,
  setSettingsSnapshot,
  buildSettingsPayload,
  commitSettingsSnapshot,
})

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
          <ProtocolHeader @refresh="refreshProtocols" @create="openCreateProtocol" />
          <ProtocolCardsSection
            :protocol-tab="protocolTab"
            :filtered-protocol-cards="filteredProtocolCards"
            @set-tab="setProtocolTab"
            @create="openCreateProtocol"
            @details="openProtocolDetails"
            @delete="openProtocolDelete"
          />
        </section>

<section v-else class="page">
            <SettingsHeader
              :settings-dirty="settingsDirty"
              :settings-saving="settingsSaving"
              @discard="discardSettings"
              @save="saveSettings"
            />
            <SettingsPanels
              :settings-tab="settingsTab"
              :ui-language="uiLanguage"
              :ui-theme="uiTheme"
              :auto-connect-on-start="autoConnectOnStart"
              :dsl-workspace-path="dslWorkspacePath"
              :language-options="languageOptions"
              :theme-options="themeOptions"
              @set-tab="setSettingsTab"
              @choose-dsl-workspace="chooseDslWorkspace"
              @update:ui-language="uiLanguage = $event"
              @update:ui-theme="uiTheme = $event"
              @update:auto-connect-on-start="autoConnectOnStart = $event"
            />
        </section>

        <ChannelDialogModal
          :open="channelDialogOpen"
          :mode="channelDialogMode"
          :channel-type="channelType"
          :channel-name="channelName"
          :channel-port="channelPort"
          :channel-baud="channelBaud"
          :channel-data-bits="channelDataBits"
          :channel-parity="channelParity"
          :channel-stop-bits="channelStopBits"
          :channel-flow-control="channelFlowControl"
          :channel-read-timeout="channelReadTimeout"
          :channel-write-timeout="channelWriteTimeout"
          :channel-host="channelHost"
          :channel-tcp-port="channelTcpPort"
          :channel-auto-connect="channelAutoConnect"
          :has-ports="ports.length > 0"
          :port-options-list="portOptionsList"
          :supported-baud-rates="supportedBaudRates"
          @close="closeChannelDialog"
          @submit="submitChannelDialog"
          @update:channel-type="channelType = $event"
          @update:channel-name="channelName = $event"
          @update:channel-port="channelPort = $event"
          @update:channel-baud="channelBaud = $event"
          @update:channel-data-bits="channelDataBits = $event"
          @update:channel-parity="channelParity = $event"
          @update:channel-stop-bits="channelStopBits = $event"
          @update:channel-flow-control="channelFlowControl = $event"
          @update:channel-read-timeout="channelReadTimeout = $event"
          @update:channel-write-timeout="channelWriteTimeout = $event"
          @update:channel-host="channelHost = $event"
          @update:channel-tcp-port="channelTcpPort = $event"
          @update:channel-auto-connect="channelAutoConnect = $event"
        />

      <teleport to="body">
        <ProtocolEditModal
          :open="protocolDialogOpen"
          :mode="protocolDialogMode"
          :draft="protocolDraft"
          :editing="protocolEditing"
          @close="closeProtocolDialog"
          @save="saveProtocol"
          @update-draft="updateProtocolDraft"
        />

        <ProtocolDeleteModal
          :open="protocolDeleteOpen"
          :deleting="protocolDeleting"
          @close="closeProtocolDelete"
          @confirm="confirmProtocolDelete"
        />
      </teleport>

      <teleport to="body">
        <UiYamlPreviewModal :open="uiModalOpen" :runtime="uiRuntime" @close="closeUiYamlModal" />
      </teleport>

</main>
    </div>

    <div v-if="snapPreview" class="snap-overlay" :class="`snap-${snapPreview}`"></div>
  </div>
</template>


