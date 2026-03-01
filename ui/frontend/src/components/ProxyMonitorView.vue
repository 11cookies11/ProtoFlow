<script setup>
import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ProxyCaptureTable from './proxy/ProxyCaptureTable.vue'
import ProxyCaptureDetails from './proxy/ProxyCaptureDetails.vue'
import ProxyCaptureToolbar from './proxy/ProxyCaptureToolbar.vue'
import ProxyCaptureFooter from './proxy/ProxyCaptureFooter.vue'
import ProxyDeleteConfirmModal from './proxy/ProxyDeleteConfirmModal.vue'
import ProxyEditModal from './proxy/ProxyEditModal.vue'
import { fallbackPorts, serialDefaults, supportedBaudRates } from '@/config/runtimeDefaults'
import { normalizeSerialPortList, normalizeSerialPortName } from '@/utils/serialPort'
import { useCapturePanel } from '@/composables/useCapturePanel'
import { useWindowedList } from '@/composables/useWindowedList'

const t = inject('t', (key) => key)
const tr = inject('tr', (text) => text)
const bridge = inject('bridge', null)

const filterTabs = computed(() => [
  { id: 'all', label: t('filter.all') },
  { id: 'running', label: t('filter.running') },
  { id: 'stopped', label: t('filter.stopped') },
  { id: 'error', label: t('filter.error') },
])
const activeFilter = ref(filterTabs.value[0]?.id ?? 'all')
const modalOpen = ref(false)
const modalProxy = ref(null)
const modalMode = ref('edit')
const confirmOpen = ref(false)
const confirmProxy = ref(null)
const captureProxy = ref(null)
const captureView = ref('parsed')
const { captureOpen, captureFilter, selectedFrame, openCapture, closeCapture } = useCapturePanel()
const captureTableRef = ref(null)

const proxyName = ref('')
const connectionMode = ref(tr('透传模式'))
const hostPort = ref(fallbackPorts[2] || fallbackPorts[0])
const devicePort = ref(fallbackPorts[4] || fallbackPorts[1] || fallbackPorts[0])
const baudRate = ref(String(serialDefaults.baud))
const parity = ref('none')
const dataBits = ref('8')
const stopBits = ref('1')
const flowControl = ref('none')

const connectionOptions = computed(() => [
  { value: '透传模式', label: tr('透传模式') },
  { value: '协议桥接', label: tr('协议桥接') },
  { value: '映射模式', label: tr('映射模式') },
])
const serialPorts = ref([])
const portOptions = computed(() => {
  const ports = normalizeSerialPortList(serialPorts.value)
  return ports.length ? ports : fallbackPorts
})
const baudOptions = supportedBaudRates.map((item) => String(item))
const parityOptions = computed(() => [
  { value: 'none', label: tr('无') },
  { value: 'even', label: tr('偶校验') },
  { value: 'odd', label: tr('奇校验') },
  { value: 'mark', label: 'Mark' },
  { value: 'space', label: 'Space' },
])

const proxies = ref([])
const formError = ref('')

let proxySeq = 1000

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

function withBridgeResult(result, onSuccess) {
  if (!result) return
  if (typeof result.then === 'function') {
    result.then(onSuccess).catch(() => {})
    return
  }
  onSuccess(result)
}

function mapProxyFromBackend(payload) {
  const status = payload.status || 'stopped'
  const active = status === 'running'
  const isError = status === 'error'
  const statusLabel = active ? tr('运行中') : isError ? tr('异常') : tr('已停止')
  const routeLabel = active ? tr('转发中') : isError ? tr('连接失败') : tr('离线')
  const routeTone = active ? 'primary' : isError ? 'danger' : 'muted'
  const statusIcon = active ? 'swap_horizontal_circle' : isError ? 'error' : 'pause_circle'
  const routeIcon = active ? 'keyboard_double_arrow_right' : isError ? 'error' : 'more_horiz'
  const baud = payload.baud ? String(payload.baud) : '115200'
  const error = typeof payload.error === 'string' ? payload.error.trim() : ''
  proxySeq = Math.max(proxySeq, Number(String(payload.id || '').replace(/\D/g, '')) || proxySeq)
  const parityMap = {
    无: 'none',
    偶校验: 'even',
    奇校验: 'odd',
    Mark: 'mark',
    Space: 'space',
  }
  const parityValue = String(payload.parity || 'none')
  const normalizedParity = parityMap[parityValue] || parityValue
  return {
    id: payload.id || `proxy-${Date.now()}`,
    name: payload.name || tr('未命名转发对'),
    meta: payload.meta || buildProxyMeta(payload.hostPort, baud),
    status,
    statusLabel,
    statusIcon,
    routeIcon,
    routeLabel,
    routeTone,
    hostPort: normalizeSerialPortName(payload.hostPort || fallbackPorts[0]),
    devicePort: normalizeSerialPortName(payload.devicePort || fallbackPorts[1] || fallbackPorts[0]),
    baud,
    dataBits: payload.dataBits || '8',
    stopBits: payload.stopBits || '1',
    parity: normalizedParity,
    flowControl: payload.flowControl || 'none',
    bandwidth: payload.bandwidth || '0.0',
    bandwidthUnit: payload.bandwidthUnit || 'KB/s',
    spark: payload.spark || '',
    error,
    active,
    toggleLabel: statusLabel,
  }
}

function loadProxyPairs() {
  if (!bridge || !bridge.value || !bridge.value.list_proxy_pairs) return
  withBridgeResult(bridge.value.list_proxy_pairs(), (items) => {
    if (!Array.isArray(items)) return
    proxies.value = items.filter(Boolean).map((item) => mapProxyFromBackend(item))
  })
}

function loadSerialPorts() {
  if (!bridge || !bridge.value || !bridge.value.list_ports) {
    serialPorts.value = []
    return
  }
  withBridgeResult(bridge.value.list_ports(), (items) => {
    if (!Array.isArray(items)) {
      serialPorts.value = []
      return
    }
    serialPorts.value = normalizeSerialPortList(items)
  })
}

const filteredProxies = computed(() => {
  const safeProxies = proxies.value.filter(Boolean)
  if (activeFilter.value === 'all') return safeProxies
  return safeProxies.filter((proxy) => proxy.status === activeFilter.value)
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

const activeFrame = computed(() => selectedFrame.value || captureFrames.value[0] || null)

const isUnknownFrame = computed(() => activeFrame.value?.protocolType === 'unknown')

const activeProtocolLabel = computed(() => activeFrame.value?.protocolLabel || '')

const activeProtocolTooltip = computed(() => activeFrame.value?.protocolTooltip || '')

const proxyStatusLabel = (status) => {
  if (status === 'running') return tr('运行中')
  if (status === 'stopped') return tr('已停止')
  if (status === 'error') return tr('异常')
  return tr('未知')
}

const proxyRouteLabel = (status) => {
  if (status === 'running') return tr('转发中')
  if (status === 'stopped') return tr('离线')
  if (status === 'error') return tr('连接失败')
  return tr('未知')
}

const proxyToggleLabel = (status) => {
  if (status === 'running') return tr('运行中')
  if (status === 'stopped') return tr('已停止')
  if (status === 'error') return tr('异常')
  return tr('未知')
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
  if (captureFilter.value === 'all') return safeFrames
  if (captureFilter.value === 'error') {
    return safeFrames.filter((frame) => frame.tone === 'red')
  }
  return safeFrames.filter((frame) => frame.direction === captureFilter.value)
})

const frameWindow = useWindowedList({
  itemCount: computed(() => filteredFrames.value.length),
  rowHeight: 36,
  overscan: 12,
  minVisibleRows: 24,
})

const visibleFrames = computed(() => {
  const { start, end } = frameWindow.range.value
  return filteredFrames.value.slice(start, end)
})

function syncCaptureWindow() {
  if (!captureTableRef.value) return
  frameWindow.updateViewport(captureTableRef.value.clientHeight || 0, captureTableRef.value.scrollTop || 0)
}

function openEditModal(proxy) {
  formError.value = ''
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
  formError.value = ''
  modalMode.value = 'create'
  modalProxy.value = null
  proxyName.value = ''
  const options = portOptions.value
  hostPort.value = options[0] || fallbackPorts[0]
  devicePort.value = options[1] || options[0] || fallbackPorts[1] || fallbackPorts[0]
  baudRate.value = baudOptions[baudOptions.length - 1] || String(serialDefaults.baud)
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
  openCapture(captureFrames.value[0] || null)
}

function closeModal() {
  formError.value = ''
  modalOpen.value = false
}

function closeCaptureModal() {
  if (bridge && bridge.value && bridge.value.stop_capture) {
    bridge.value.stop_capture()
  }
  closeCapture()
}

function selectFrame(frame) {
  selectedFrame.value = frame
}

function refreshProxies() {
  loadSerialPorts()
  if (bridge && bridge.value && bridge.value.refresh_proxy_pairs) {
    withBridgeResult(bridge.value.refresh_proxy_pairs(), (items) => {
      if (!Array.isArray(items)) return
      proxies.value = items.map((item) => mapProxyFromBackend(item))
    })
    return
  }
  proxies.value = proxies.value.map((proxy) => ({ ...proxy }))
}

function validateProxyPayload(payload) {
  if (!payload.hostPort || !payload.devicePort) {
    return tr('请选择主机端口和设备端口')
  }
  if (payload.hostPort === payload.devicePort) {
    return tr('主机端口和设备端口不能相同')
  }
  return ''
}

function setProxyStatus(proxy, active) {
  const nextStatus = active ? 'running' : 'stopped'
  const statusLabel = active ? tr('运行中') : tr('已停止')
  const routeLabel = active ? tr('转发中') : tr('离线')
  const routeTone = active ? 'primary' : 'muted'
  const statusIcon = active ? 'swap_horizontal_circle' : 'pause_circle'
  const routeIcon = active ? 'keyboard_double_arrow_right' : 'more_horiz'
  proxy.status = nextStatus
  proxy.statusLabel = statusLabel
  proxy.toggleLabel = statusLabel
  proxy.routeLabel = routeLabel
  proxy.routeTone = routeTone
  proxy.statusIcon = statusIcon
  proxy.routeIcon = routeIcon
  proxy.error = ''
  proxy.active = active

  if (bridge && bridge.value && bridge.value.set_proxy_pair_status) {
    withBridgeResult(bridge.value.set_proxy_pair_status(proxy.id, active), (updated) => {
      if (updated && typeof updated === 'object') {
        Object.assign(proxy, mapProxyFromBackend(updated))
      }
    })
  }
}

function retryProxy(proxy) {
  if (!proxy) return
  setProxyStatus(proxy, true)
}

function saveProxy() {
  const payload = {
    name: proxyName.value || tr('未命名转发对'),
    hostPort: normalizeSerialPortName(hostPort.value),
    devicePort: normalizeSerialPortName(devicePort.value),
    baud: baudRate.value,
    dataBits: dataBits.value,
    stopBits: stopBits.value,
    parity: parity.value,
    flowControl: flowControl.value,
  }
  const validationError = validateProxyPayload(payload)
  if (validationError) {
    formError.value = validationError
    return
  }
  formError.value = ''

  if (modalMode.value === 'create') {
    if (bridge && bridge.value && bridge.value.create_proxy_pair) {
      withBridgeResult(
        bridge.value.create_proxy_pair({
          name: payload.name,
          hostPort: payload.hostPort,
          devicePort: payload.devicePort,
          baud: payload.baud,
          dataBits: payload.dataBits,
          stopBits: payload.stopBits,
          parity: payload.parity,
          flowControl: payload.flowControl,
        }),
        (created) => {
          if (created) {
            proxies.value.unshift(mapProxyFromBackend(created))
          }
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
          dataBits: payload.dataBits,
          stopBits: payload.stopBits,
          parity: payload.parity,
          flowControl: payload.flowControl,
          status: modalProxy.value.status,
        }),
        (updated) => {
          if (updated) {
            Object.assign(modalProxy.value, mapProxyFromBackend(updated))
          }
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
  loadSerialPorts()
  loadProxyPairs()
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
    withBridgeResult(bridge.value.delete_proxy_pair(proxy.id), (success) => {
      if (success) {
        proxies.value = proxies.value.filter((item) => item.id !== proxy.id)
      }
    })
  } else {
    proxies.value = proxies.value.filter((item) => item.id !== proxy.id)
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
    if (!open) {
      frameWindow.reset()
      return
    }
    nextTick(() => syncCaptureWindow())
  }
)

watch(
  () => filteredFrames.value.length,
  () => {
    nextTick(() => syncCaptureWindow())
  }
)

onBeforeUnmount(() => {
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
        :class="`status-${proxy.status}`"
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
            {{ proxyStatusLabel(proxy.status) }}
          </span>
        </div>

        <div class="proxy-route-card" :class="`status-${proxy.status}`">
          <div class="proxy-route-col">
            <p>{{ tr('主机源端口') }}</p>
            <span class="proxy-route-chip proxy-mono">{{ proxy.hostPort }}</span>
          </div>
          <div class="proxy-route-state" :class="proxy.routeTone">
            <span class="material-symbols-outlined">{{ proxy.routeIcon }}</span>
            <span>{{ proxyRouteLabel(proxy.status) }}</span>
          </div>
          <div class="proxy-route-col">
            <p>{{ tr('设备代理端口') }}</p>
            <span class="proxy-route-chip proxy-mono">{{ proxy.devicePort }}</span>
          </div>
        </div>

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

        <div v-if="proxy.status === 'error'" class="proxy-error-hint">
          <div class="proxy-error-message">
            <span class="material-symbols-outlined">warning</span>
            <span>{{ proxy.error || tr('代理启动失败，请检查端口占用和参数配置。') }}</span>
          </div>
          <button class="proxy-error-retry" type="button" @click="retryProxy(proxy)">
            <span class="material-symbols-outlined">refresh</span>
            {{ tr('重试') }}
          </button>
        </div>

        <div class="proxy-panel-footer" :class="`status-${proxy.status}`">
          <label class="proxy-footer-toggle">
            <span class="proxy-toggle" :class="{ active: proxy.active }" @click="setProxyStatus(proxy, !proxy.active)">
              <span class="proxy-toggle-track"></span>
            </span>
            <span class="proxy-toggle-text">{{ proxyToggleLabel(proxy.status) }}</span>
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
  </section>

  <teleport to="body">
    <ProxyEditModal
      :open="modalOpen"
      :mode="modalMode"
      :form-error="formError"
      :proxy-name="proxyName"
      :connection-mode="connectionMode"
      :host-port="hostPort"
      :device-port="devicePort"
      :baud-rate="baudRate"
      :data-bits="dataBits"
      :stop-bits="stopBits"
      :parity="parity"
      :flow-control="flowControl"
      :connection-options="connectionOptions"
      :port-options="portOptions"
      :baud-options="baudOptions"
      :parity-options="parityOptions"
      @close="closeModal"
      @save="saveProxy"
      @update:proxy-name="proxyName = $event"
      @update:connection-mode="connectionMode = $event"
      @update:host-port="hostPort = $event"
      @update:device-port="devicePort = $event"
      @update:baud-rate="baudRate = $event"
      @update:data-bits="dataBits = $event"
      @update:stop-bits="stopBits = $event"
      @update:parity="parity = $event"
      @update:flow-control="flowControl = $event"
    />

    <div v-if="captureOpen" class="proxy-modal-overlay proxy-capture" @mousedown.self="closeCaptureModal">
      <div
        class="packet-modal w-full max-w-[1600px] h-screen md:h-[96vh] bg-[var(--bg-light)] shadow-2xl md:rounded-xl flex flex-col overflow-hidden border border-slate-200"
        @mousedown.stop
        @click.stop
      >
        <ProxyCaptureToolbar :capture-proxy="captureProxy" :capture-meta="captureMeta" />

        <main class="flex-1 flex overflow-hidden">
          <div ref="captureTableRef" class="flex-[2] min-w-0 overflow-auto" @scroll.passive="syncCaptureWindow">
            <ProxyCaptureTable
              :visible-frames="visibleFrames"
              :capture-meta="captureMeta"
              :frame-window="frameWindow"
              @select-frame="selectFrame"
            />
          </div>

          <ProxyCaptureDetails
            :active-frame="activeFrame"
            :is-unknown-frame="isUnknownFrame"
            :active-protocol-label="activeProtocolLabel"
            :active-hex-size="activeHexSize"
            :active-hex-cells="activeHexCells"
            :active-hex-ascii="activeHexAscii"
            :active-tree-rows="activeTreeRows"
            :capture-metrics="captureMetrics"
            :hex-cell-class="hexCellClass"
            @close="closeCaptureModal"
          />
        </main>
        <ProxyCaptureFooter :capture-meta="captureMeta" />
      </div>
    </div>

    <ProxyDeleteConfirmModal
      :open="confirmOpen"
      :confirm-proxy="confirmProxy"
      @close="closeConfirm"
      @confirm="applyConfirmDelete"
    />
  </teleport>
</template>
