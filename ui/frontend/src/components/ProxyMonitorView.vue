<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import DropdownSelect from './DropdownSelect.vue'

const t = inject('t', (key) => key)
const tr = inject('tr', (text) => text)
const bridge = inject('bridge', null)

const filterTabs = computed(() => [
  { id: 'all', label: t('filter.all') },
  { id: 'running', label: t('filter.running') },
  { id: 'configured', label: tr('已配置') },
  { id: 'stopped', label: t('filter.stopped') },
  { id: 'error', label: t('filter.error') },
])
const activeFilter = ref(filterTabs.value[0]?.id ?? 'all')
const modalOpen = ref(false)
const modalProxy = ref(null)
const modalMode = ref('edit')
const captureOpen = ref(false)
const confirmOpen = ref(false)
const confirmProxy = ref(null)
const captureProxy = ref(null)
const captureFilter = ref('all')
const captureView = ref('parsed')
const captureSearch = ref('')
const capturePage = ref(1)
const selectedFrame = ref(null)
const CAPTURE_PAGE_SIZE = 50
const notices = ref([])
let noticeSeq = 0

const proxyName = ref('')
const connectionMode = ref(tr('透传模式'))
const hostPort = ref('COM3')
const devicePort = ref('COM5')
const baudRate = ref('115200')
const parity = ref(tr('无'))
const dataBits = ref('8')
const stopBits = ref('1')
const flowControl = ref('none')

const connectionOptions = computed(() => [
  { value: '透传模式', label: tr('透传模式') },
  { value: '协议桥接', label: tr('协议桥接') },
  { value: '映射模式', label: tr('映射模式') },
])
const portOptions = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM10', 'COM12']
const baudOptions = ['4800', '9600', '19200', '38400', '57600', '115200']
const parityOptions = computed(() => [
  { value: '无', label: tr('无') },
  { value: '偶校验', label: tr('偶校验') },
  { value: '奇校验', label: tr('奇校验') },
  { value: 'Mark', label: 'Mark' },
  { value: 'Space', label: 'Space' },
])


const proxies = ref([])

let proxySeq = 1000
let proxyPairsSignalHandler = null
let captureFrameSignalHandler = null

const bandwidthWindowSec = ref(30)
const bandwidthWindowOptions = [10, 30, 60]
const SPARK_BUCKETS = 10
const SAMPLE_RETENTION_SEC = 180
const channelTrafficSamples = new Map()

function normalizeChannel(value) {
  return String(value || '')
    .trim()
    .toUpperCase()
}

function buildSparklinePath(values) {
  if (!Array.isArray(values) || !values.length) return ''
  const points = values.map((value) => Math.max(0, Number(value) || 0))
  const max = Math.max(...points, 1)
  const step = points.length > 1 ? 100 / (points.length - 1) : 100
  return points
    .map((value, index) => {
      const x = (index * step).toFixed(2)
      const y = (38 - (value / max) * 30).toFixed(2)
      return `${index === 0 ? 'M' : 'L'}${x} ${y}`
    })
    .join(' ')
}

function appendTrafficSample(payload) {
  if (!payload || typeof payload !== 'object') return
  const channel = normalizeChannel(payload.channel)
  const size = Math.max(0, Number(payload.length || 0))
  if (!channel || !size) return
  const ts = Number(payload.timestamp || Date.now() / 1000)
  const list = channelTrafficSamples.get(channel) || []
  list.push({ ts, size })
  const keepFrom = ts - SAMPLE_RETENTION_SEC
  while (list.length && list[0].ts < keepFrom) {
    list.shift()
  }
  channelTrafficSamples.set(channel, list)
}

function formatBandwidth(bytesPerSec) {
  const safe = Math.max(0, Number(bytesPerSec) || 0)
  if (safe >= 1024 * 1024) {
    const value = safe / (1024 * 1024)
    return { value: value >= 10 ? value.toFixed(1) : value.toFixed(2), unit: 'MB/s' }
  }
  if (safe >= 1024) {
    const value = safe / 1024
    return { value: value >= 10 ? value.toFixed(1) : value.toFixed(2), unit: 'KB/s' }
  }
  return { value: String(Math.round(safe)), unit: 'B/s' }
}

function buildProxyMeta(host, baud) {
  return `ID: PX-${proxySeq} · ${baud ? String(baud) : '8'}-N-1`
}

function normalizeProxy(proxy, updates = {}) {
  const next = { ...proxy, ...updates }
  if (!next.meta) {
    next.meta = buildProxyMeta(next.hostPort, next.baud)
  }
  return next
}

function pushNotice(level, message) {
  const id = `notice-${Date.now()}-${noticeSeq++}`
  notices.value.push({ id, level, message })
  window.setTimeout(() => {
    notices.value = notices.value.filter((item) => item.id !== id)
  }, 2500)
}

function withBridgeResult(result, onSuccess, onError) {
  if (!result) return
  if (typeof result.then === 'function') {
    result.then(onSuccess).catch((err) => {
      if (typeof onError === 'function') onError(err)
    })
    return
  }
  onSuccess(result)
}

function deriveProxyPresentation(status, capability = 'config-only') {
  if (status === 'error') {
    return {
      statusLabel: tr('异常'),
      routeLabel: tr('连接失败'),
      routeTone: 'danger',
      statusIcon: 'report',
      routeIcon: 'sync_problem',
      toggleLabel: tr('异常'),
    }
  }
  if (status === 'configured') {
    return {
      statusLabel: tr('配置已启用'),
      routeLabel: tr('未建立实时转发'),
      routeTone: 'primary',
      statusIcon: 'tune',
      routeIcon: 'keyboard_double_arrow_right',
      toggleLabel: tr('已启用'),
    }
  }
  if (status === 'running') {
    if (capability === 'realtime-forward') {
      return {
        statusLabel: tr('运行中'),
        routeLabel: tr('转发中'),
        routeTone: 'primary',
        statusIcon: 'swap_horizontal_circle',
        routeIcon: 'keyboard_double_arrow_right',
        toggleLabel: tr('运行中'),
      }
    }
    return {
      statusLabel: tr('配置已启用'),
      routeLabel: tr('未建立实时转发'),
      routeTone: 'primary',
      statusIcon: 'swap_horizontal_circle',
      routeIcon: 'keyboard_double_arrow_right',
      toggleLabel: tr('已启用'),
    }
  }
  return {
    statusLabel: tr('已停止'),
    routeLabel: tr('离线'),
    routeTone: 'muted',
    statusIcon: 'pause_circle',
    routeIcon: 'more_horiz',
    toggleLabel: tr('已停止'),
  }
}

function mapProxyFromBackend(payload) {
  const status = payload.status || 'stopped'
  const active = status === 'running' || status === 'configured'
  const capability = payload.capability || 'config-only'
  const view = deriveProxyPresentation(status, capability)
  const baud = payload.baud ? String(payload.baud) : '115200'
  proxySeq = Math.max(proxySeq, Number(String(payload.id || '').replace(/\D/g, '')) || proxySeq)
  return {
    id: payload.id || `proxy-${Date.now()}`,
    name: payload.name || tr('未命名转发对'),
    meta: payload.meta || buildProxyMeta(payload.hostPort, baud),
    status,
    capability,
    statusLabel: view.statusLabel,
    statusIcon: view.statusIcon,
    routeIcon: view.routeIcon,
    routeLabel: view.routeLabel,
    routeTone: view.routeTone,
    hostPort: payload.hostPort || 'COM1',
    devicePort: payload.devicePort || 'COM2',
    baud,
    dataBits: payload.dataBits || '8',
    stopBits: payload.stopBits || '1',
    parity: payload.parity || 'none',
    flowControl: payload.flowControl || 'none',
    bandwidth: payload.bandwidth || '0.0',
    bandwidthUnit: payload.bandwidthUnit || 'KB/s',
    spark: payload.spark || '',
    active,
    toggleLabel: view.toggleLabel,
  }
}

function mergeProxyRuntimeMetrics(nextProxy) {
  const current = proxies.value.find((item) => item.id === nextProxy.id)
  if (!current) return nextProxy
  return {
    ...nextProxy,
    bandwidth: current.bandwidth || nextProxy.bandwidth,
    bandwidthUnit: current.bandwidthUnit || nextProxy.bandwidthUnit,
    spark: current.spark || nextProxy.spark,
  }
}

function applyProxyListFromBackend(items) {
  proxies.value = items
    .filter(Boolean)
    .map((item) => mergeProxyRuntimeMetrics(mapProxyFromBackend(item)))
  if (captureProxy.value?.id) {
    const matched = proxies.value.find((proxy) => proxy.id === captureProxy.value.id)
    if (matched) {
      captureProxy.value = matched
    }
  }
  refreshProxyRuntimeMetrics()
}

function loadProxyPairs() {
  if (!bridge || !bridge.value || !bridge.value.list_proxy_pairs) return
  withBridgeResult(bridge.value.list_proxy_pairs(), (items) => {
    if (!Array.isArray(items)) return
    applyProxyListFromBackend(items)
  })
}

function refreshProxyRuntimeMetrics() {
  if (!proxies.value.length) return
  const nowSec = Date.now() / 1000
  const windowSec = Math.max(1, Number(bandwidthWindowSec.value) || 30)
  const lowerBound = nowSec - windowSec

  proxies.value = proxies.value.map((proxy) => {
    const host = normalizeChannel(proxy.hostPort)
    const device = normalizeChannel(proxy.devicePort)
    const samples = [...(channelTrafficSamples.get(host) || []), ...(channelTrafficSamples.get(device) || [])]
      .filter((sample) => sample.ts >= lowerBound)
      .sort((a, b) => a.ts - b.ts)

    if (!samples.length) {
      return {
        ...proxy,
        bandwidth: '0',
        bandwidthUnit: 'B/s',
        spark: '',
      }
    }

    const bytes = samples.reduce((sum, sample) => sum + sample.size, 0)
    const bytesPerSec = bytes / windowSec
    const display = formatBandwidth(bytesPerSec)
    const bucketSec = windowSec / SPARK_BUCKETS
    const buckets = new Array(SPARK_BUCKETS).fill(0)
    for (const sample of samples) {
      const idx = Math.min(
        SPARK_BUCKETS - 1,
        Math.max(0, Math.floor((sample.ts - lowerBound) / bucketSec))
      )
      buckets[idx] += sample.size
    }
    const bucketRates = buckets.map((value) => value / bucketSec)
    return {
      ...proxy,
      bandwidth: display.value,
      bandwidthUnit: display.unit,
      spark: buildSparklinePath(bucketRates),
    }
  })
}

function attachProxyPairsSignal() {
  if (!bridge || !bridge.value || !bridge.value.proxy_pairs) return
  if (proxyPairsSignalHandler) return
  proxyPairsSignalHandler = (items) => {
    if (!Array.isArray(items)) return
    applyProxyListFromBackend(items)
  }
  bridge.value.proxy_pairs.connect(proxyPairsSignalHandler)
}

function detachProxyPairsSignal() {
  if (!bridge || !bridge.value || !bridge.value.proxy_pairs || !proxyPairsSignalHandler) return
  try {
    bridge.value.proxy_pairs.disconnect(proxyPairsSignalHandler)
  } catch (_) {}
  proxyPairsSignalHandler = null
}

function attachCaptureFrameSignal() {
  if (!bridge || !bridge.value || !bridge.value.capture_frame) return
  if (captureFrameSignalHandler) return
  captureFrameSignalHandler = (payload) => {
    appendTrafficSample(payload)
    refreshProxyRuntimeMetrics()
  }
  bridge.value.capture_frame.connect(captureFrameSignalHandler)
}

function detachCaptureFrameSignal() {
  if (!bridge || !bridge.value || !bridge.value.capture_frame || !captureFrameSignalHandler) return
  try {
    bridge.value.capture_frame.disconnect(captureFrameSignalHandler)
  } catch (_) {}
  captureFrameSignalHandler = null
}

const filteredProxies = computed(() => {
  const safeProxies = proxies.value.filter(Boolean)
  if (activeFilter.value === 'all') return safeProxies
  if (activeFilter.value === 'running') {
    return safeProxies.filter((proxy) => proxy.status === 'running' || proxy.status === 'configured')
  }
  return safeProxies.filter((proxy) => proxy.status === activeFilter.value)
})

const proxyStats = computed(() => {
  const safeProxies = proxies.value.filter(Boolean)
  return {
    total: safeProxies.length,
    running: safeProxies.filter((proxy) => proxy.status === 'running').length,
    configured: safeProxies.filter((proxy) => proxy.status === 'configured').length,
    error: safeProxies.filter((proxy) => proxy.status === 'error').length,
  }
})

const props = defineProps({
  captureFrames: {
    type: Array,
    default: () => [],
  },
  captureMeta: {
    type: Object,
    default: () => ({}),
  },
  captureMetrics: {
    type: Object,
    default: () => ({}),
  },
})

const captureFrames = computed(() => props.captureFrames || [])

const captureMeta = computed(() => ({
  bufferUsed: 0,
  rangeStart: 0,
  rangeEnd: 0,
  totalFrames: 0,
  page: 1,
  pageCount: 1,
  channel: '',
  engine: '',
  ...(props.captureMeta || {}),
}))

const captureMetrics = computed(() => ({
  rtt: '',
  loss: '',
  ...(props.captureMetrics || {}),
}))

const isCaptureRunning = computed(() => {
  const engine = String(captureMeta.value.engine || '').toLowerCase()
  return engine.includes('running') || engine.includes('运行中')
})

const captureChannelNormalized = computed(() => {
  return normalizeChannel(captureMeta.value.channel || captureProxy.value?.hostPort || '')
})

const captureExpectedChannels = computed(() => {
  if (!captureProxy.value) return []
  return [normalizeChannel(captureProxy.value.hostPort), normalizeChannel(captureProxy.value.devicePort)].filter(Boolean)
})

const captureChannelMismatch = computed(() => {
  if (!captureOpen.value || !captureProxy.value) return false
  const channel = captureChannelNormalized.value
  if (!channel) return false
  return !captureExpectedChannels.value.includes(channel)
})

const captureChannelHint = computed(() => {
  if (!captureChannelMismatch.value || !captureProxy.value) return ''
  return `${tr('当前抓包通道与代理端口不一致')}: ${captureMeta.value.channel}`
})

function isProxyCaptureActive(proxy) {
  if (!proxy || !isCaptureRunning.value) return false
  const host = normalizeChannel(proxy.hostPort)
  const device = normalizeChannel(proxy.devicePort)
  const activeChannel = captureChannelNormalized.value
  return Boolean(activeChannel) && (activeChannel === host || activeChannel === device)
}

const activeFrame = computed(() => selectedFrame.value || captureFrames.value[0] || null)

const isUnknownFrame = computed(() => activeFrame.value?.protocolType === 'unknown')

const activeProtocolLabel = computed(() => activeFrame.value?.protocolLabel || '')

const activeProtocolTooltip = computed(() => activeFrame.value?.protocolTooltip || '')

const proxyStatusLabel = (status, capability = 'config-only') => {
  return deriveProxyPresentation(status, capability).statusLabel || tr('未知')
}

const proxyRouteLabel = (status, capability = 'config-only') => {
  return deriveProxyPresentation(status, capability).routeLabel || tr('未知')
}

const proxyToggleLabel = (status, capability = 'config-only') => {
  return deriveProxyPresentation(status, capability).toggleLabel || tr('未知')
}

const activeSummaryText = computed(() => activeFrame.value?.summaryText || activeFrame.value?.summary || '')

const activeHexBytes = computed(() => {
  const hexDump = activeFrame.value?.hexDump
  if (hexDump && Array.isArray(hexDump.bytes) && hexDump.bytes.length) {
    return hexDump.bytes.map((part) => String(part || '').toUpperCase())
  }
  const raw = activeFrame.value?.note || ''
  const parts = raw
    .trim()
    .split(/\s+/)
    .filter((item) => item.length)
  return parts.map((part) => part.toUpperCase())
})

const activeHexCells = computed(() => {
  const bytes = activeHexBytes.value.slice(0, 16)
  if (!bytes.length) return []
  while (bytes.length < 16) bytes.push('--')
  return bytes
})

const activeHexAscii = computed(() => {
  if (!activeHexCells.value.length) return ['', '']
  const bytes = activeHexCells.value.map((cell) => {
    if (cell === '--') return '.'
    const code = parseInt(cell, 16)
    if (!Number.isFinite(code)) return '.'
    return code >= 32 && code <= 126 ? String.fromCharCode(code) : '.'
  })
  return [bytes.slice(0, 8).join(''), bytes.slice(8, 16).join('')]
})

const activeHexSize = computed(() => {
  const hexDump = activeFrame.value?.hexDump
  if (hexDump && typeof hexDump.size === 'number') return hexDump.size
  return activeHexBytes.value.length || 0
})

const activeTreeRows = computed(() => {
  const rows = activeFrame.value?.tree
  if (Array.isArray(rows) && rows.length) {
    return rows.map((row) => ({
      label: row.label || row.name || '',
      raw: row.raw || row.raw_hex || '',
      value: row.value || row.display || '',
    }))
  }
  return []
})

function hexCellClass(index, value) {
  if (value === '--') return 'text-slate-300'
  if (index < 2) return 'text-blue-500 bg-blue-50 rounded'
  if (index === 3 || index === 4) return 'text-emerald-500 font-bold bg-emerald-50 rounded'
  if (index === 5 || index === 6) return 'text-amber-500 font-bold bg-amber-50 rounded'
  return 'text-slate-400'
}

const filteredFrames = computed(() => {
  const safeFrames = captureFrames.value.filter(Boolean)
  const byType = (() => {
    if (captureFilter.value === 'all') return safeFrames
    if (captureFilter.value === 'error') {
      return safeFrames.filter((frame) => frame.tone === 'red')
    }
    return safeFrames.filter((frame) => frame.direction === captureFilter.value)
  })()
  const keyword = String(captureSearch.value || '').trim().toLowerCase()
  if (!keyword) return byType
  return byType.filter((frame) => {
    const text = [
      frame?.id,
      frame?.note,
      frame?.summaryText,
      frame?.summary,
      frame?.protocolLabel,
      frame?.direction,
      frame?.time,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return text.includes(keyword)
  })
})

const capturePageCount = computed(() => {
  const total = filteredFrames.value.length
  return Math.max(1, Math.ceil(total / CAPTURE_PAGE_SIZE))
})

const pagedFrames = computed(() => {
  const page = Math.min(Math.max(1, capturePage.value), capturePageCount.value)
  const start = (page - 1) * CAPTURE_PAGE_SIZE
  const end = start + CAPTURE_PAGE_SIZE
  return filteredFrames.value.slice(start, end)
})

const pageRangeStart = computed(() => {
  if (!filteredFrames.value.length) return 0
  return (Math.min(Math.max(1, capturePage.value), capturePageCount.value) - 1) * CAPTURE_PAGE_SIZE + 1
})

const pageRangeEnd = computed(() => {
  if (!filteredFrames.value.length) return 0
  return Math.min(pageRangeStart.value + pagedFrames.value.length - 1, filteredFrames.value.length)
})

function goFirstPage() {
  capturePage.value = 1
}

function goPrevPage() {
  capturePage.value = Math.max(1, capturePage.value - 1)
}

function goNextPage() {
  capturePage.value = Math.min(capturePageCount.value, capturePage.value + 1)
}

function goLastPage() {
  capturePage.value = capturePageCount.value
}

function exportAnalysis() {
  const exportedAt = new Date().toISOString()
  const filename = `capture_analysis_${exportedAt.replace(/[:.]/g, '-')}.json`
  const payload = {
    exportedAt,
    proxy: captureProxy.value ? { id: captureProxy.value.id, name: captureProxy.value.name } : null,
    filter: captureFilter.value,
    keyword: captureSearch.value,
    page: capturePage.value,
    pageSize: CAPTURE_PAGE_SIZE,
    totalFiltered: filteredFrames.value.length,
    frames: filteredFrames.value,
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function openEditModal(proxy) {
  modalMode.value = 'edit'
  modalProxy.value = proxy
  proxyName.value = proxy && proxy.name ? proxy.name : ''
  hostPort.value = proxy && proxy.hostPort ? proxy.hostPort : hostPort.value
  devicePort.value = proxy && proxy.devicePort ? proxy.devicePort : devicePort.value
  baudRate.value = proxy && proxy.baud ? String(proxy.baud) : baudRate.value
  dataBits.value = proxy && proxy.dataBits ? String(proxy.dataBits) : dataBits.value
  stopBits.value = proxy && proxy.stopBits ? String(proxy.stopBits) : stopBits.value
  parity.value = proxy && proxy.parity ? String(proxy.parity) : parity.value
  flowControl.value = proxy && proxy.flowControl ? String(proxy.flowControl) : flowControl.value
  modalOpen.value = true
}

function openCreateModal() {
  modalMode.value = 'create'
  modalProxy.value = null
  proxyName.value = ''
  hostPort.value = portOptions[0] || 'COM1'
  devicePort.value = portOptions[1] || 'COM2'
  baudRate.value = baudOptions[5] || '115200'
  dataBits.value = '8'
  stopBits.value = '1'
  parity.value = 'none'
  flowControl.value = 'none'
  modalOpen.value = true
}

function openCaptureModal(proxy) {
  if (bridge && bridge.value && bridge.value.start_capture) {
    bridge.value.start_capture({
      id: proxy?.id,
      channel: proxy?.hostPort,
      hostPort: proxy?.hostPort,
    })
  }
  captureProxy.value = proxy
  captureFilter.value = 'all'
  captureSearch.value = ''
  capturePage.value = 1
  selectedFrame.value = captureFrames.value[0] || null
  captureOpen.value = true
}

function closeModal() {
  modalOpen.value = false
}

function closeCaptureModal() {
  if (bridge && bridge.value && bridge.value.stop_capture) {
    bridge.value.stop_capture()
  }
  captureOpen.value = false
}

function toggleCaptureEngine() {
  if (!bridge || !bridge.value) return
  if (isCaptureRunning.value) {
    if (bridge.value.stop_capture) {
      bridge.value.stop_capture()
    }
    return
  }
  if (bridge.value.start_capture) {
    bridge.value.start_capture({
      id: captureProxy.value?.id,
      channel: captureProxy.value?.hostPort || captureMeta.value.channel || '',
      hostPort: captureProxy.value?.hostPort || '',
    })
  }
}

function selectFrame(frame) {
  selectedFrame.value = frame
}

function refreshProxies() {
  if (bridge && bridge.value && bridge.value.refresh_proxy_pairs) {
    withBridgeResult(
      bridge.value.refresh_proxy_pairs(),
      (items) => {
        if (!Array.isArray(items)) return
        applyProxyListFromBackend(items)
        pushNotice('success', tr('代理状态已刷新'))
      },
      () => {
        pushNotice('error', tr('刷新代理状态失败'))
      }
    )
    return
  }
  refreshProxyRuntimeMetrics()
}

function setProxyStatus(proxy, active) {
  const capability = proxy.capability || 'config-only'
  const nextStatus = active
    ? (capability === 'realtime-forward' ? 'running' : 'configured')
    : 'stopped'
  const view = deriveProxyPresentation(nextStatus, capability)
  proxy.status = nextStatus
  proxy.statusLabel = view.statusLabel
  proxy.toggleLabel = view.toggleLabel
  proxy.routeLabel = view.routeLabel
  proxy.routeTone = view.routeTone
  proxy.statusIcon = view.statusIcon
  proxy.routeIcon = view.routeIcon
  proxy.active = active

  if (bridge && bridge.value && bridge.value.set_proxy_pair_status) {
    withBridgeResult(
      bridge.value.set_proxy_pair_status(proxy.id, active),
      (updated) => {
        if (updated && typeof updated === 'object') {
          Object.assign(proxy, mapProxyFromBackend(updated))
          refreshProxyRuntimeMetrics()
          pushNotice('success', active ? tr('代理已启用') : tr('代理已停用'))
        }
      },
      () => {
        pushNotice('error', tr('代理状态更新失败'))
      }
    )
  }

  if (!active && isProxyCaptureActive(proxy) && bridge && bridge.value && bridge.value.stop_capture) {
    bridge.value.stop_capture()
  }
}

function saveProxy() {
  const payload = {
    name: proxyName.value || tr('未命名转发对'),
    hostPort: hostPort.value,
    devicePort: devicePort.value,
    baud: baudRate.value,
    dataBits: dataBits.value,
    stopBits: stopBits.value,
    parity: parity.value,
    flowControl: flowControl.value,
  }

  if (modalMode.value === 'create') {
    if (bridge && bridge.value && bridge.value.create_proxy_pair) {
      withBridgeResult(
        bridge.value.create_proxy_pair({
          name: payload.name,
          hostPort: payload.hostPort,
          devicePort: payload.devicePort,
          baud: payload.baud,
          capability: 'config-only',
          dataBits: payload.dataBits,
          stopBits: payload.stopBits,
          parity: payload.parity,
          flowControl: payload.flowControl,
        }),
        (created) => {
          if (created) {
            proxies.value.unshift(mergeProxyRuntimeMetrics(mapProxyFromBackend(created)))
            refreshProxyRuntimeMetrics()
            pushNotice('success', tr('代理创建成功'))
          }
        },
        () => {
          pushNotice('error', tr('代理创建失败'))
        }
      )
    } else {
      proxySeq += 1
      const newProxy = normalizeProxy(
        {
          id: `proxy-${proxySeq}`,
          name: payload.name,
          meta: buildProxyMeta(payload.hostPort, payload.baud),
          status: 'stopped',
          statusLabel: tr('已停止'),
          statusIcon: 'pause_circle',
          routeIcon: 'more_horiz',
          routeLabel: tr('离线'),
          routeTone: 'muted',
          hostPort: payload.hostPort,
          devicePort: payload.devicePort,
          baud: payload.baud,
          dataBits: payload.dataBits,
          stopBits: payload.stopBits,
          parity: payload.parity,
          flowControl: payload.flowControl,
          bandwidth: '0.0',
          bandwidthUnit: 'KB/s',
          spark: '',
          active: false,
          toggleLabel: tr('已停止'),
        },
        {}
      )
      proxies.value.unshift(newProxy)
    }
  } else if (modalProxy.value) {
    if (bridge && bridge.value && bridge.value.update_proxy_pair) {
      withBridgeResult(
        bridge.value.update_proxy_pair({
          id: modalProxy.value.id,
          name: payload.name,
          hostPort: payload.hostPort,
          devicePort: payload.devicePort,
          baud: payload.baud,
          capability: modalProxy.value.capability || 'config-only',
          dataBits: payload.dataBits,
          stopBits: payload.stopBits,
          parity: payload.parity,
          flowControl: payload.flowControl,
          status: modalProxy.value.status,
        }),
        (updated) => {
          if (updated) {
            Object.assign(modalProxy.value, mapProxyFromBackend(updated))
            refreshProxyRuntimeMetrics()
            pushNotice('success', tr('代理保存成功'))
          }
        },
        () => {
          pushNotice('error', tr('代理保存失败'))
        }
      )
    } else {
      modalProxy.value.name = payload.name
      modalProxy.value.hostPort = payload.hostPort
      modalProxy.value.devicePort = payload.devicePort
      modalProxy.value.baud = payload.baud
      modalProxy.value.dataBits = payload.dataBits
      modalProxy.value.stopBits = payload.stopBits
      modalProxy.value.parity = payload.parity
      modalProxy.value.flowControl = payload.flowControl
      modalProxy.value.meta = buildProxyMeta(payload.hostPort, payload.baud)
    }
  }

  modalOpen.value = false
}

function confirmDeleteProxy(proxy) {
  if (!proxy) return
  confirmProxy.value = proxy
  confirmOpen.value = true
}

onMounted(() => {
  attachProxyPairsSignal()
  attachCaptureFrameSignal()
  loadProxyPairs()
  refreshProxyRuntimeMetrics()
})

function closeConfirm() {
  confirmOpen.value = false
  confirmProxy.value = null
}

function applyConfirmDelete() {
  const proxy = confirmProxy.value
  if (!proxy) return
  setProxyStatus(proxy, false)
  if (bridge && bridge.value && bridge.value.delete_proxy_pair) {
    withBridgeResult(
      bridge.value.delete_proxy_pair(proxy.id),
      (success) => {
        if (success) {
          proxies.value = proxies.value.filter((item) => item.id !== proxy.id)
          pushNotice('success', tr('代理删除成功'))
        } else {
          pushNotice('error', tr('代理删除失败'))
        }
      },
      () => {
        pushNotice('error', tr('代理删除失败'))
      }
    )
  } else {
    proxies.value = proxies.value.filter((item) => item.id !== proxy.id)
    pushNotice('success', tr('代理删除成功'))
  }
  closeConfirm()
}

watch(
  () => modalOpen.value,
  (open) => {
    document.body.classList.toggle('proxy-edit-open', open)
  }
)

watch(
  () => captureOpen.value,
  (open) => {
    document.body.classList.toggle('proxy-modal-open', open)
  }
)

watch(
  () => [captureFilter.value, captureSearch.value, filteredFrames.value.length],
  () => {
    capturePage.value = 1
  }
)

watch(
  () => [capturePage.value, capturePageCount.value],
  () => {
    if (capturePage.value > capturePageCount.value) {
      capturePage.value = capturePageCount.value
    }
    if (capturePage.value < 1) {
      capturePage.value = 1
    }
  }
)

watch(
  () => bridge && bridge.value,
  () => {
    detachProxyPairsSignal()
    detachCaptureFrameSignal()
    attachProxyPairsSignal()
    attachCaptureFrameSignal()
  }
)

watch(
  () => proxies.value.map((proxy) => `${proxy.id}:${proxy.hostPort}:${proxy.devicePort}`).join('|'),
  () => {
    refreshProxyRuntimeMetrics()
  }
)

watch(
  () => bandwidthWindowSec.value,
  () => {
    refreshProxyRuntimeMetrics()
  }
)

onBeforeUnmount(() => {
  detachProxyPairsSignal()
  detachCaptureFrameSignal()
  document.body.classList.remove('proxy-edit-open')
  document.body.classList.remove('proxy-modal-open')
})
</script>

<template>
  <section class="page proxy-page proxy-dashboard">
    <header class="page-header spaced">
      <div>
        <h2>{{ t('header.proxy.title') }}</h2>
        <p>{{ t('header.proxy.desc') }}</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" type="button" @click="refreshProxies">
          <span class="material-symbols-outlined">refresh</span>
          {{ t('action.refreshStatus') }}
        </button>
        <button class="btn btn-primary" type="button" @click="openCreateModal">
          <span class="material-symbols-outlined">add</span>
          {{ t('action.newProxy') }}
        </button>
      </div>
    </header>
    <p class="proxy-capability-note">
      {{ tr('说明：当前版本以代理配置管理和抓包分析为主，状态“配置已启用”不代表已建立实时串口转发链路。') }}
    </p>
    <div class="proxy-dashboard-filters">
      <span class="proxy-filter-chip active">{{ tr('总数') }}: {{ proxyStats.total }}</span>
      <span class="proxy-filter-chip">{{ tr('运行中') }}: {{ proxyStats.running }}</span>
      <span class="proxy-filter-chip">{{ tr('已配置') }}: {{ proxyStats.configured }}</span>
      <span class="proxy-filter-chip">{{ tr('异常') }}: {{ proxyStats.error }}</span>
      <span class="proxy-filter-chip">
        {{ tr('统计窗口') }}:
        <button
          v-for="option in bandwidthWindowOptions"
          :key="`win-${option}`"
          type="button"
          :class="{ active: bandwidthWindowSec === option }"
          @click="bandwidthWindowSec = option"
          style="margin-left: 6px; padding: 2px 6px; border-radius: 999px; border: 1px solid rgba(15,23,42,0.16)"
        >
          {{ option }}s
        </button>
      </span>
    </div>
    <div class="tab-strip secondary">
      <button
        v-for="tab in filterTabs"
        :key="tab.id"
        type="button"
        :class="{ active: activeFilter === tab.id }"
        @click="activeFilter = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="proxy-dashboard-grid">
      <article
        v-for="proxy in filteredProxies"
        :key="proxy.id"
        class="proxy-panel"
        :class="[
          `status-${proxy.status}`,
          {
            'capture-active': isProxyCaptureActive(proxy),
            'capture-selected': captureOpen && captureProxy && captureProxy.id === proxy.id,
          },
        ]"
        :style="
          isProxyCaptureActive(proxy)
            ? 'outline: 2px solid rgba(59,130,246,0.45); outline-offset: 2px;'
            : (captureOpen && captureProxy && captureProxy.id === proxy.id
                ? 'outline: 2px solid rgba(16,185,129,0.45); outline-offset: 2px;'
                : '')
        "
      >
        <div class="proxy-panel-head">
          <div class="proxy-panel-title">
            <div class="proxy-panel-icon" :class="`status-${proxy.status}`">
              <span class="material-symbols-outlined">{{ proxy.statusIcon }}</span>
            </div>
            <div>
            <h3>{{ tr(proxy.name) }}</h3>
              <p>{{ proxy.meta }}</p>
            </div>
          </div>
          <span class="proxy-status-pill" :class="`status-${proxy.status}`">
            <span class="dot"></span>
            {{ proxyStatusLabel(proxy.status, proxy.capability) }}
          </span>
        </div>

        <div class="proxy-route-card" :class="`status-${proxy.status}`">
          <div class="proxy-route-col">
            <p>{{ tr('主机源端口') }}</p>
            <span class="proxy-route-chip proxy-mono">{{ proxy.hostPort }}</span>
          </div>
          <div class="proxy-route-state" :class="proxy.routeTone">
            <span class="material-symbols-outlined">{{ proxy.routeIcon }}</span>
            <span>{{ proxyRouteLabel(proxy.status, proxy.capability) }}</span>
          </div>
          <div class="proxy-route-col">
            <p>{{ tr('设备代理端口') }}</p>
            <span class="proxy-route-chip proxy-mono">{{ proxy.devicePort }}</span>
          </div>
        </div>
        <p v-if="isProxyCaptureActive(proxy)" class="proxy-capability-note">{{ tr('抓包中') }}</p>

        <div class="proxy-metrics">
          <div>
            <p>{{ tr('波特率') }}</p>
            <strong class="proxy-mono">{{ proxy.baud }}</strong>
          </div>
          <div class="proxy-metric-bandwidth">
            <div>
              <p :class="{ danger: proxy.status === 'error' }">{{ tr('实时带宽') }}</p>
              <strong class="proxy-mono">
                {{ proxy.bandwidth }}
                <span>{{ proxy.bandwidthUnit }}</span>
              </strong>
            </div>
            <div class="proxy-sparkline" :class="`status-${proxy.status}`">
              <svg v-if="proxy.spark" viewBox="0 0 100 40">
                <path :d="proxy.spark" />
              </svg>
              <div v-else class="proxy-sparkline-empty"></div>
            </div>
          </div>
        </div>

        <div class="proxy-panel-footer" :class="`status-${proxy.status}`">
          <label class="proxy-footer-toggle">
            <span class="proxy-toggle" :class="{ active: proxy.active }" @click="setProxyStatus(proxy, !proxy.active)">
              <span class="proxy-toggle-track"></span>
            </span>
            <span class="proxy-toggle-text">{{ proxyToggleLabel(proxy.status, proxy.capability) }}</span>
          </label>
          <div class="proxy-footer-actions">
            <button class="icon-btn" type="button" :title="tr('抓包')" @click="openCaptureModal(proxy)">
              <span class="material-symbols-outlined">terminal</span>
            </button>
            <button class="icon-btn" type="button" :title="tr('编辑')" @click="openEditModal(proxy)">
              <span class="material-symbols-outlined">edit</span>
            </button>
            <button class="icon-btn danger" type="button" :title="tr('删除')" @click="confirmDeleteProxy(proxy)">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </div>
        </div>
      </article>
    </div>
    <div
      v-if="notices.length"
      style="position: fixed; right: 20px; bottom: 20px; z-index: 80; display: flex; flex-direction: column; gap: 8px;"
    >
      <div
        v-for="notice in notices"
        :key="notice.id"
        :style="
          `padding: 8px 12px; border-radius: 10px; font-size: 12px; font-weight: 600; color: #fff; box-shadow: 0 8px 20px rgba(2,6,23,.2); background: ${
            notice.level === 'error' ? '#dc2626' : '#0f766e'
          }`
        "
      >
        {{ notice.message }}
      </div>
    </div>
  </section>

  <teleport to="body">
    <div v-if="modalOpen" class="proxy-modal-overlay">
      <div class="proxy-modal" @mousedown.stop @click.stop>
        <div class="proxy-modal-header">
          <div class="proxy-modal-title">
            <div class="proxy-modal-icon">
              <span class="material-symbols-outlined">edit_square</span>
            </div>
            <h2>{{ modalMode === 'create' ? tr('新建转发对') : tr('编辑转发代理') }}</h2>
          </div>
          <button class="proxy-modal-close" type="button" @click="closeModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="proxy-modal-body">
          <div class="proxy-modal-stack">
            <div class="proxy-modal-grid">
              <div class="proxy-field">
                <label>{{ tr('代理名称') }}</label>
                <input type="text" v-model="proxyName" />
              </div>
              <div class="proxy-field">
                <label>{{ tr('连接模式') }}</label>
                <DropdownSelect v-model="connectionMode" class="proxy-select" :options="connectionOptions" />
              </div>
            </div>
            <div class="proxy-port-map">
              <div class="proxy-field">
                <label>
                <span class="material-symbols-outlined">computer</span>{{ tr('主机端口') }}</label>
                <DropdownSelect v-model="hostPort" class="proxy-select" :options="portOptions" />
              </div>
              <div class="proxy-field">
                <label>
                  <span class="material-symbols-outlined">settings_input_component</span>{{ tr('设备端口') }}</label>
                <DropdownSelect v-model="devicePort" class="proxy-select" :options="portOptions" />
              </div>
            </div>
            <div class="proxy-section">
              <div class="proxy-section-title">
                <span class="material-symbols-outlined">settings_ethernet</span>{{ tr('串口参数配置') }}<span>{{ tr('（两端需一致）') }}</span>
              </div>
              <div class="proxy-section-grid">
                <div class="proxy-field">
                  <label>{{ tr('波特率') }}</label>
                  <DropdownSelect v-model="baudRate" class="proxy-select" :options="baudOptions" />
                </div>
                <div class="proxy-field">
                  <label>{{ tr('数据位') }}</label>
                  <div class="proxy-segmented">
                    <button type="button" :class="{ active: dataBits === '5' }" @click="dataBits = '5'">5</button>
                    <button type="button" :class="{ active: dataBits === '6' }" @click="dataBits = '6'">6</button>
                    <button type="button" :class="{ active: dataBits === '7' }" @click="dataBits = '7'">7</button>
                    <button type="button" :class="{ active: dataBits === '8' }" @click="dataBits = '8'">8</button>
                  </div>
                </div>
                <div class="proxy-field">
                  <label>{{ tr('校验位') }}</label>
                  <DropdownSelect v-model="parity" class="proxy-select" :options="parityOptions" />
                </div>
                <div class="proxy-field">
                  <label>{{ tr('停止位') }}</label>
                  <div class="proxy-segmented">
                    <button type="button" :class="{ active: stopBits === '1' }" @click="stopBits = '1'">1</button>
                    <button type="button" :class="{ active: stopBits === '1.5' }" @click="stopBits = '1.5'">1.5</button>
                    <button type="button" :class="{ active: stopBits === '2' }" @click="stopBits = '2'">2</button>
                  </div>
                </div>
                <div class="proxy-field proxy-span-2">
                  <label>{{ tr('流控') }}</label>
                  <div class="proxy-segmented">
                    <button type="button" :class="{ active: flowControl === 'none' }" @click="flowControl = 'none'">None</button>
                    <button type="button" :class="{ active: flowControl === 'rtscts' }" @click="flowControl = 'rtscts'">RTS/CTS</button>
                    <button type="button" :class="{ active: flowControl === 'xonxoff' }" @click="flowControl = 'xonxoff'">XON/XOFF</button>
                  </div>
                </div>
              </div>
            </div>
            <div class="proxy-section proxy-modal-advanced">
              <div class="proxy-section-title muted">
                <span class="material-symbols-outlined">settings_suggest</span>{{ tr('高级选项') }}</div>
              <div class="proxy-toggle-row">
                <label>
                  <span class="proxy-toggle">
                    <input type="checkbox" checked />
                    <span></span>
                  </span>{{ tr('自动重连') }}</label>
                <label>
                  <span class="proxy-toggle">
                    <input type="checkbox" />
                    <span></span>
                  </span>{{ tr('详细日志') }}</label>
              </div>
            </div>
          </div>
        </div>
        <div class="proxy-modal-footer">
          <div></div>
          <div class="proxy-footer-actions">
            <button class="proxy-btn ghost" type="button" @click="closeModal">{{ tr('取消') }}</button>
            <button class="proxy-btn primary" type="button" @click="saveProxy">{{ tr('保存') }}</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="captureOpen" class="proxy-modal-overlay proxy-capture" @mousedown.self="closeCaptureModal">
      <div
        class="packet-modal w-full max-w-[1600px] h-screen md:h-[96vh] bg-[var(--bg-light)] shadow-2xl md:rounded-xl flex flex-col overflow-hidden border border-slate-200"
        @mousedown.stop
        @click.stop
      >
        <header class="px-4 py-3 flex items-center justify-between border-b border-slate-200 bg-white">
          <div class="flex items-center gap-4">
            <div class="p-1.5 bg-blue-100 rounded text-blue-600">
              <span class="material-symbols-outlined">analytics</span>
            </div>
            <div>
              <h1 class="text-sm font-bold text-slate-900 leading-none">{{ tr('多协议通用报文分析引擎') }}</h1>
              <div class="flex items-center gap-2 mt-1">
                <span class="flex h-2 w-2 rounded-full bg-emerald-500"></span>
                <p class="text-[10px] font-medium text-slate-500">
                  {{ tr('活动通道') }}: {{ captureProxy ? captureProxy.hostPort : captureMeta.channel }} | {{ tr('引擎状态') }}: {{ tr(captureMeta.engine) }}
                </p>
                <p v-if="captureChannelMismatch" class="text-[10px] font-medium text-rose-600 mt-1">
                  {{ captureChannelHint }}
                </p>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="flex items-center bg-slate-100 rounded-md px-2 border border-slate-200">
              <span class="material-symbols-outlined text-slate-400">search</span>
              <input
                class="bg-transparent border-none text-xs w-64 lg:w-96 focus:ring-0 text-slate-900 placeholder-slate-500"
                :placeholder="tr('搜索标识、十六进制、协议、原始数据...')"
                v-model="captureSearch"
                type="text"
              />
            </div>
            <div class="h-6 w-[1px] bg-slate-200 mx-1"></div>
            <button
              class="flex items-center gap-1 px-3 py-1.5 text-white rounded text-xs font-bold transition-colors shadow-sm"
              :class="isCaptureRunning ? 'bg-amber-600 hover:bg-amber-700' : 'bg-emerald-600 hover:bg-emerald-700'"
              @click="toggleCaptureEngine"
            >
              <span class="material-symbols-outlined !text-sm">{{ isCaptureRunning ? 'pause' : 'play_arrow' }}</span>
              {{ isCaptureRunning ? tr('暂停捕获') : tr('继续捕获') }}
            </button>
            <button class="p-1.5 hover:bg-slate-100 rounded text-slate-400">
              <span class="material-symbols-outlined">settings</span>
            </button>
          </div>
        </header>

        <div class="h-1.5 w-full bg-slate-200 relative cursor-pointer group overflow-hidden">
          <div class="timeline-heatmap h-full w-full opacity-80 group-hover:opacity-100 transition-opacity"></div>
          <div class="absolute top-0 bottom-0 left-[20%] w-[5%] border-x border-white/50 bg-white/20 shadow-sm pointer-events-none"></div>
        </div>

        <main class="flex-1 flex overflow-hidden">
          <section class="flex-[2] flex flex-col min-w-0 bg-white">
            <div class="overflow-auto flex-1">
              <table class="w-full text-left border-separate border-spacing-0">
                <thead class="sticky top-0 z-10 bg-slate-50 shadow-sm">
                  <tr class="text-[10px] uppercase tracking-wider font-bold text-slate-500">
                    <th class="px-3 py-2 border-b border-slate-200 w-16">{{ tr('序号') }}</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-28">{{ tr('时间戳') }}</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-12 text-center">{{ tr('方向') }}</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-32">{{ tr('协议') }}</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-16">{{ tr('长度') }}</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-72">{{ tr('原始数据') }}</th>
                    <th class="px-3 py-2 border-b border-slate-200">{{ tr('摘要 (解析结果/HEX/ASCII)') }}</th>
                  </tr>
                </thead>
                <tbody class="text-xs">
                  <tr
                    v-for="(frame, index) in pagedFrames"
                    :key="frame?.id ?? index"
                    class="hover:bg-slate-50 cursor-pointer border-b border-slate-100"
                    :class="{ 'bg-orange-50/40 border-l-4 border-l-orange-400': frame.tone === 'red' }"
                    @click="selectFrame(frame)"
                  >
                    <td class="px-3 py-2 text-slate-400 font-mono">
                      {{ frame.seq ?? (pageRangeStart ? pageRangeStart + index : index + 1) }}
                    </td>
                    <td class="px-3 py-2 text-slate-500 font-mono">{{ frame.time }}</td>
                    <td class="px-3 py-2 text-center">
                      <span
                        class="material-symbols-outlined !text-sm"
                        :class="frame.direction === 'RX' ? 'text-emerald-500' : 'text-blue-500'"
                      >
                        {{ frame.direction === 'RX' ? 'arrow_downward' : 'arrow_upward' }}
                      </span>
                    </td>
                    <td class="px-3 py-2">
                      <div class="relative inline-block protocol-badge">
                        <div
                          class="flex items-center gap-1.5 px-2 py-0.5 rounded-full font-bold text-[9px] border"
                          :class="
                            frame.tone === 'red'
                              ? 'bg-slate-100 text-slate-600 border-dashed border-slate-300'
                              : 'bg-blue-100 text-blue-800 border-blue-200'
                          "
                        >
                          <span
                            class="w-3.5 h-3.5 flex items-center justify-center text-white rounded-full text-[8px] font-black"
                            :class="frame.tone === 'red' ? 'bg-slate-400' : 'bg-blue-600'"
                          >
                            {{ frame.tone === 'red' ? '?' : 'M' }}
                          </span>
                          <span>{{ frame.protocolLabel || '' }}</span>
                        </div>
                        <div class="protocol-tooltip bg-slate-800 text-white text-[10px] px-2 py-1 rounded shadow-lg pointer-events-none whitespace-nowrap border border-slate-700">
                          {{ frame.protocolTooltip || '' }}
                        </div>
                      </div>
                    </td>
                    <td class="px-3 py-2 text-slate-500">{{ frame.size }}B</td>
                    <td class="px-3 py-2 hex-font text-slate-400 truncate max-w-[240px]">{{ frame.note }}</td>
                    <td class="px-3 py-2 text-slate-600 italic">
                      {{ frame.summaryText || frame.summary || '' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <aside class="flex-1 w-[450px] flex flex-col border-l border-slate-200 bg-slate-50">
            <div class="px-4 py-3 border-b border-slate-200 flex justify-between items-center bg-white shadow-sm">
              <h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                <span class="material-symbols-outlined !text-sm text-blue-500">info</span>{{ tr('报文解析详情') }}</h2>
              <div class="flex gap-2">
                <button class="p-1 hover:bg-slate-100 rounded" :title="tr('复制原始十六进制')">
                  <span class="material-symbols-outlined !text-sm">content_copy</span>
                </button>
                <button class="p-1 hover:bg-slate-100 rounded" @click="closeCaptureModal">
                  <span class="material-symbols-outlined !text-sm">close</span>
                </button>
              </div>
            </div>
            <div class="flex-1 overflow-y-auto">
              <div v-if="!activeFrame" class="p-6 text-center text-slate-400 text-sm">{{ tr('暂无报文数据') }}</div>
              <template v-else>
                <div class="p-6 text-center space-y-4 border-b border-slate-200 bg-orange-50/20">
                  <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-orange-100 text-orange-600 mb-1">
                    <span class="material-symbols-outlined !text-3xl">question_mark</span>
                  </div>
                  <div>
                    <h3 class="text-sm font-bold text-slate-800">
                      {{ isUnknownFrame ? tr('未知协议报文 (Unknown Protocol)') : `${activeProtocolLabel} ${tr('报文')}` }}
                    </h3>
                    <p class="text-[11px] text-slate-500 mt-1 max-w-[280px] mx-auto leading-relaxed">
                      {{
                        isUnknownFrame
                          ? tr('系统未能自动匹配已知的解析插件。您可以尝试手动配置解析规则，或使用万能解析脚本。')
                          : tr('已匹配协议解析插件，当前展示该报文的解析详情。')
                      }}
                    </p>
                  </div>
                  <div class="flex justify-center gap-3">
                    <button class="px-3 py-1.5 bg-white border border-slate-300 rounded text-[11px] font-bold hover:bg-slate-50 transition-colors shadow-sm">
                      {{ isUnknownFrame ? tr('手动解析') : tr('查看详情') }}
                    </button>
                    <button class="px-3 py-1.5 bg-blue-600 text-white rounded text-[11px] font-bold hover:bg-blue-700 transition-colors flex items-center gap-1 shadow-md">
                      <span class="material-symbols-outlined !text-xs">schema</span>
                      {{ isUnknownFrame ? tr('配置解析规则') : tr('调整解析规则') }}
                    </button>
                  </div>
                </div>
                <div class="p-4 border-b border-slate-200">
                  <div class="flex items-center justify-between mb-3">
                    <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{{ tr('原始十六进制 (RAW HEX)') }}</h3>
                    <span class="text-[10px] font-mono bg-slate-200 px-1.5 py-0.5 rounded text-slate-600">
                      {{ activeHexSize }} {{ tr('字节') }}
                    </span>
                  </div>
                  <div v-if="activeHexCells.length" class="bg-white border border-slate-200 rounded-lg overflow-hidden flex shadow-inner">
                    <div class="bg-slate-50 border-r border-slate-200 p-2 text-[10px] font-mono text-slate-400 leading-6 text-right w-12 shrink-0">
                      0000<br />0008
                    </div>
                    <div class="flex-1 p-2 hex-font text-xs leading-6 grid grid-cols-8 gap-x-1 text-center font-medium">
                      <span
                        v-for="(cell, cellIndex) in activeHexCells"
                        :key="`hex-${cellIndex}`"
                        :class="hexCellClass(cellIndex, cell)"
                      >
                        {{ cell }}
                      </span>
                    </div>
                    <div class="border-l border-slate-200 p-2 text-[10px] font-mono text-slate-500 leading-6 tracking-tight w-24 shrink-0 bg-slate-50/50">
                      {{ activeHexAscii[0] }}<br />{{ activeHexAscii[1] }}
                    </div>
                  </div>
                  <div v-else class="text-xs text-slate-400">{{ tr('暂无十六进制数据') }}</div>
                </div>
                <div class="p-4 space-y-4">
                  <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">{{ tr('协议层级解析 (PROTOCOL TREE)') }}</h3>
                  <div class="relative pl-4 space-y-1">
                    <div class="flex items-center gap-2 -ml-4 cursor-pointer hover:bg-slate-100 p-1 rounded transition-colors group">
                      <span class="material-symbols-outlined text-slate-400 group-open:rotate-90">arrow_right</span>
                      <span class="text-[11px] font-bold text-slate-500 uppercase">{{ tr('链路层 (Data Link Layer)') }}</span>
                    </div>
                    <div class="tree-line relative pl-2 space-y-1">
                      <details class="group" open>
                        <summary class="flex items-center gap-2 list-none cursor-pointer hover:bg-slate-100 p-1 rounded -ml-4 transition-colors">
                          <span class="material-symbols-outlined text-blue-500 group-open:rotate-90 transition-transform">arrow_drop_down</span>
                          <span class="text-[11px] font-bold text-slate-800 uppercase">{{ activeProtocolLabel }}</span>
                        </summary>
                        <div class="mt-2 space-y-0.5 pl-2">
                          <div class="grid grid-cols-12 text-[9px] font-bold text-slate-400 px-2 py-1 uppercase tracking-tighter">
                            <div class="col-span-3">{{ tr('原始值') }}</div>
                            <div class="col-span-4">{{ tr('字段') }}</div>
                            <div class="col-span-5 text-right">{{ tr('解析值') }}</div>
                          </div>
                          <div
                            v-for="(row, rowIndex) in activeTreeRows"
                            :key="`tree-${rowIndex}`"
                            class="grid grid-cols-12 items-center py-1.5 px-2 rounded hover:bg-blue-50 cursor-default transition-colors border-l-2 border-transparent hover:border-blue-500"
                          >
                            <div class="col-span-3 font-mono text-[11px] text-blue-600">{{ row.raw }}</div>
                            <div class="col-span-4 text-[11px] text-slate-500">{{ row.label }}</div>
                            <div class="col-span-5 text-[11px] text-right font-bold text-slate-700">{{ row.value }}</div>
                          </div>
                          <div v-if="!activeTreeRows.length" class="text-xs text-slate-400 px-2 py-2">{{ tr('暂无协议解析数据') }}</div>
                        </div>
                      </details>
                    </div>
                  </div>
                </div>
              </template>
            </div>
            <div class="p-4 bg-slate-100/50 border-t border-slate-200">
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">{{ tr('实时网络指标') }}</p>
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-white p-2 rounded border border-slate-200 shadow-sm">
                  <p class="text-[9px] text-slate-500">{{ tr('往返延时 (RTT)') }}</p>
                  <p class="text-sm font-bold text-emerald-500">{{ captureMetrics.rtt }}</p>
                </div>
                <div class="bg-white p-2 rounded border border-slate-200 shadow-sm">
                  <p class="text-[9px] text-slate-500">{{ tr('丢包率 (Packet Loss)') }}</p>
                  <p class="text-sm font-bold text-slate-900">{{ captureMetrics.loss }}</p>
                </div>
              </div>
            </div>
          </aside>
        </main>
        <footer class="px-4 py-2 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <span class="text-[10px] font-bold text-slate-500 uppercase">{{ tr('接收缓冲区') }}</span>
              <div class="w-32 h-2 bg-slate-200 rounded-full overflow-hidden border border-slate-300">
                <div class="h-full bg-amber-500" :style="{ width: `${captureMeta.bufferUsed}%` }"></div>
              </div>
              <span class="text-[10px] font-mono font-bold text-slate-600">{{ captureMeta.bufferUsed }}%</span>
            </div>
            <div class="h-4 w-[1px] bg-slate-300"></div>
            <p class="text-[10px] font-medium text-slate-500 uppercase">
              {{ tr('显示') }} {{ pageRangeStart }}-{{ pageRangeEnd }} / {{ tr('共') }} {{ filteredFrames.length }} {{ tr('报文') }}
            </p>
          </div>
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-1 bg-white p-0.5 rounded border border-slate-200">
              <button class="p-1 hover:bg-slate-100 rounded" :disabled="capturePage <= 1" @click="goFirstPage">
                <span class="material-symbols-outlined !text-sm">first_page</span>
              </button>
              <button class="p-1 hover:bg-slate-100 rounded" :disabled="capturePage <= 1" @click="goPrevPage">
                <span class="material-symbols-outlined !text-sm">chevron_left</span>
              </button>
              <div class="px-3 text-[10px] font-bold text-slate-700">{{ tr('第') }} {{ capturePage }} / {{ capturePageCount }} {{ tr('页') }}</div>
              <button class="p-1 hover:bg-slate-100 rounded" :disabled="capturePage >= capturePageCount" @click="goNextPage">
                <span class="material-symbols-outlined !text-sm">chevron_right</span>
              </button>
              <button class="p-1 hover:bg-slate-100 rounded" :disabled="capturePage >= capturePageCount" @click="goLastPage">
                <span class="material-symbols-outlined !text-sm">last_page</span>
              </button>
            </div>
            <button class="flex items-center gap-1 px-3 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded text-[10px] font-bold transition-colors" @click="exportAnalysis">
              <span class="material-symbols-outlined !text-sm">download</span>{{ tr('导出分析结果') }}</button>
          </div>
        </footer>
      </div>
    </div>

    <div v-if="confirmOpen" class="proxy-modal-overlay" @mousedown.self="closeConfirm">
      <div class="proxy-modal proxy-confirm-modal" @mousedown.stop @click.stop>
        <div class="proxy-modal-header">
          <div class="proxy-modal-title">
            <div class="proxy-modal-icon">
              <span class="material-symbols-outlined">warning</span>
            </div>
            <h2>{{ tr('确认删除') }}</h2>
          </div>
          <button class="proxy-modal-close" type="button" @click="closeConfirm">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="proxy-modal-body">
          <p class="proxy-confirm-text">
            {{ tr('确认删除转发对') }}「{{ confirmProxy?.name || tr('未命名转发对') }}」{{ tr('吗？') }}{{ tr('删除前将停止转发。') }}
          </p>
        </div>
        <div class="proxy-modal-footer">
          <div></div>
          <div class="proxy-footer-actions">
            <button class="proxy-btn ghost" type="button" @click="closeConfirm">{{ tr('取消') }}</button>
            <button class="proxy-btn warning" type="button" @click="applyConfirmDelete">{{ tr('确认删除') }}</button>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>
