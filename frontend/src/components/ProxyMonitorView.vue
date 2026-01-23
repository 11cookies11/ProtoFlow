<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import DropdownSelect from './DropdownSelect.vue'

const filterTabs = [
  { id: 'all', label: '全部' },
  { id: 'running', label: '运行中' },
  { id: 'stopped', label: '已停止' },
  { id: 'error', label: '异常' },
]
const activeFilter = ref(filterTabs[0].id)
const modalOpen = ref(false)
const modalProxy = ref(null)
const captureOpen = ref(false)
const captureProxy = ref(null)
const captureFilter = ref('all')
const captureView = ref('parsed')
const selectedProtocol = ref('Modbus RTU')
const selectedFrame = ref(null)

const protocolOptions = ['Modbus RTU', 'MQTT', 'Raw Hex', 'Custom Protocol A']

const proxyName = ref('')
const connectionMode = ref('透传模式')
const hostPort = ref('COM3')
const devicePort = ref('COM5')
const baudRate = ref('115200')
const parity = ref('无')

const connectionOptions = ['透传模式', '协议桥接', '映射模式']
const portOptions = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM10', 'COM12']
const baudOptions = ['4800', '9600', '19200', '38400', '57600', '115200']
const parityOptions = ['无', '偶校验', '奇校验', 'Mark', 'Space']

const proxies = ref([
  {
    id: 'proxy-com3',
    name: '主控制器链路',
    meta: 'ID: PX-00124 · 8-N-1',
    status: 'running',
    statusLabel: '运行中',
    statusIcon: 'swap_horizontal_circle',
    routeIcon: 'keyboard_double_arrow_right',
    routeLabel: '转发中',
    routeTone: 'primary',
    hostPort: 'COM3',
    devicePort: 'COM5',
    baud: '115200',
    bandwidth: '12.4',
    bandwidthUnit: 'KB/s',
    spark: 'M0 35 L10 20 L20 35 L30 10 L40 30 L50 5 L60 35 L70 20 L80 30 L90 10 L100 25',
    active: true,
    toggleLabel: '运行中',
  },
  {
    id: 'proxy-com7',
    name: '电机反馈继电器',
    meta: 'ID: PX-00992 · 8-E-1',
    status: 'stopped',
    statusLabel: '已停止',
    statusIcon: 'pause_circle',
    routeIcon: 'more_horiz',
    routeLabel: '离线',
    routeTone: 'muted',
    hostPort: 'COM7',
    devicePort: 'COM10',
    baud: '9600',
    bandwidth: '0.0',
    bandwidthUnit: 'KB/s',
    spark: '',
    active: false,
    toggleLabel: '已停止',
  },
  {
    id: 'proxy-com1',
    name: 'GPS 模块数据流',
    meta: 'ID: PX-00219 · 7-N-2',
    status: 'error',
    statusLabel: '异常',
    statusIcon: 'report',
    routeIcon: 'sync_problem',
    routeLabel: '连接失败',
    routeTone: 'danger',
    hostPort: 'COM1',
    devicePort: 'COM12',
    baud: '4800',
    bandwidth: '0.4',
    bandwidthUnit: 'KB/s',
    spark: 'M0 38 L40 38 L42 10 L48 10 L50 38 L90 38 L92 10 L98 10 L100 38',
    active: true,
    toggleLabel: '异常',
  },
])

const filteredProxies = computed(() => {
  if (activeFilter.value === 'all') return proxies.value
  return proxies.value.filter((proxy) => proxy.status === activeFilter.value)
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

const localCaptureFrames = ref([
  {
    id: 'frame-001',
    direction: 'RX',
    time: '14:20:01.2',
    size: 64,
    note: '01 03 00 00 00 02 C4 0B',
    summary: 'Read Hold Regs',
    summaryText: '请求: 读取保持寄存器 0x0000',
    tone: 'green',
    warn: false,
    channel: 'COM5',
    baud: '115200',
    protocolLabel: 'Modbus RTU',
    protocolType: 'modbus',
    protocolTooltip: 'Modbus RTU v1.1',
  },
  {
    id: 'frame-002',
    direction: 'TX',
    time: '14:20:01.5',
    size: 128,
    note: '01 03 04 01 F4 02 BC 9B 42',
    summary: 'Resp: 50.0 / 70.0',
    summaryText: '响应: 寄存器 0=500.0, 1=700.0',
    tone: 'blue',
    warn: false,
    channel: 'COM3',
    baud: '115200',
    protocolLabel: 'Modbus RTU',
    protocolType: 'modbus',
    protocolTooltip: 'Modbus RTU v1.1',
  },
  {
    id: 'frame-003',
    direction: 'RX',
    time: '14:20:02.8',
    size: 1,
    note: '01 83 02 FF FF',
    summary: 'EXCEPTION: ILLEGAL_ADDR',
    summaryText: '异常: 非法寄存器地址',
    tone: 'red',
    warn: true,
    channel: 'COM5',
    baud: '115200',
    protocolLabel: 'Unknown',
    protocolType: 'unknown',
    protocolTooltip: '未知协议 - 点击配置',
  },
  {
    id: 'frame-004',
    direction: 'RX',
    time: '14:20:03.2',
    size: 0,
    note: 'Waiting for next frame...',
    summary: '',
    summaryText: '等待下一帧...',
    tone: 'amber',
    warn: false,
    channel: 'COM5',
    baud: '115200',
    protocolLabel: 'Modbus RTU',
    protocolType: 'modbus',
    protocolTooltip: 'Modbus RTU v1.1',
  },
])

const localCaptureMeta = ref({
  channel: 'Ethernet (TAP)',
  engine: '通用动态解析 (Agnostic Engine)',
  bufferUsed: 85,
  rangeStart: 1,
  rangeEnd: 50,
  totalFrames: 50234,
  page: 1,
  pageCount: 1005,
})

const localCaptureMetrics = ref({
  rtt: '4.2 ms',
  loss: '0.02 %',
})

const protocolTrees = {
  modbus: [
    { label: '报文标识 (Header)', raw: '01 03', value: '0x0103' },
    { label: '数据长度 (Len)', raw: '08', value: '8 Bytes' },
  ],
  unknown: [
    { label: '报文标识 (Header)', raw: 'FF EE', value: '65518' },
    { label: '数据长度 (Len)', raw: '10', value: '16 Bytes' },
  ],
}

const captureFrames = computed(() =>
  props.captureFrames && props.captureFrames.length ? props.captureFrames : localCaptureFrames.value
)

const captureMeta = computed(() =>
  props.captureMeta && Object.keys(props.captureMeta).length ? props.captureMeta : localCaptureMeta.value
)

const captureMetrics = computed(() =>
  props.captureMetrics && Object.keys(props.captureMetrics).length ? props.captureMetrics : localCaptureMetrics.value
)

const activeFrame = computed(() => selectedFrame.value || captureFrames.value[0] || null)

const isUnknownFrame = computed(() => activeFrame.value?.protocolType === 'unknown')

const activeProtocolLabel = computed(() => activeFrame.value?.protocolLabel || selectedProtocol.value)

const activeProtocolTooltip = computed(() => activeFrame.value?.protocolTooltip || '未知协议')

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
  while (bytes.length < 16) bytes.push('--')
  return bytes
})

const activeHexAscii = computed(() => {
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
      label: row.label || row.name || '字段',
      raw: row.raw || row.raw_hex || '--',
      value: row.value || row.display || '--',
    }))
  }
  return isUnknownFrame.value ? protocolTrees.unknown : protocolTrees.modbus
})

function hexCellClass(index, value) {
  if (value === '--') return 'text-slate-300'
  if (index < 2) return 'text-blue-500 bg-blue-50 rounded'
  if (index === 3 || index === 4) return 'text-emerald-500 font-bold bg-emerald-50 rounded'
  if (index === 5 || index === 6) return 'text-amber-500 font-bold bg-amber-50 rounded'
  return 'text-slate-400'
}

const filteredFrames = computed(() => {
  if (captureFilter.value === 'all') return captureFrames.value
  if (captureFilter.value === 'error') {
    return captureFrames.value.filter((frame) => frame.tone === 'red')
  }
  return captureFrames.value.filter((frame) => frame.direction === captureFilter.value)
})

function openEditModal(proxy) {
  modalProxy.value = proxy
  proxyName.value = proxy && proxy.name ? proxy.name : ''
  hostPort.value = proxy && proxy.hostPort ? proxy.hostPort : hostPort.value
  devicePort.value = proxy && proxy.devicePort ? proxy.devicePort : devicePort.value
  baudRate.value = proxy && proxy.baud ? String(proxy.baud) : baudRate.value
  modalOpen.value = true
}

function openCaptureModal(proxy) {
  captureProxy.value = proxy
  captureFilter.value = 'all'
  selectedFrame.value = captureFrames.value[0] || null
  captureOpen.value = true
}

function closeModal() {
  modalOpen.value = false
}

function closeCaptureModal() {
  captureOpen.value = false
}

function selectFrame(frame) {
  selectedFrame.value = frame
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

onBeforeUnmount(() => {
  document.body.classList.remove('proxy-edit-open')
  document.body.classList.remove('proxy-modal-open')
})
</script>

<template>
  <section class="page proxy-page proxy-dashboard">
    <header class="proxy-dashboard-hero">
      <div class="proxy-hero-card">
        <div>
          <h2>代理监控</h2>
          <p>管理转发链路并实时监控数据流状态。</p>
        </div>
        <div class="proxy-hero-actions">
          <button class="proxy-hero-btn" type="button">
            <span class="material-symbols-outlined">refresh</span>
            刷新状态
          </button>
          <button class="proxy-hero-btn primary" type="button">
            <span class="material-symbols-outlined">add</span>
            新建转发对
          </button>
        </div>
      </div>
      <div class="proxy-dashboard-filters">
        <button
          v-for="tab in filterTabs"
          :key="tab.id"
          type="button"
          class="proxy-filter-chip"
          :class="{ active: activeFilter === tab.id }"
          @click="activeFilter = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
    </header>

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
              <h3>{{ proxy.name }}</h3>
              <p>{{ proxy.meta }}</p>
            </div>
          </div>
          <span class="proxy-status-pill" :class="`status-${proxy.status}`">
            <span class="dot"></span>
            {{ proxy.statusLabel }}
          </span>
        </div>

        <div class="proxy-route-card" :class="`status-${proxy.status}`">
          <div class="proxy-route-col">
            <p>主机源端口</p>
            <span class="proxy-route-chip proxy-mono">{{ proxy.hostPort }}</span>
          </div>
          <div class="proxy-route-state" :class="proxy.routeTone">
            <span class="material-symbols-outlined">{{ proxy.routeIcon }}</span>
            <span>{{ proxy.routeLabel }}</span>
          </div>
          <div class="proxy-route-col">
            <p>设备代理端口</p>
            <span class="proxy-route-chip proxy-mono">{{ proxy.devicePort }}</span>
          </div>
        </div>

        <div class="proxy-metrics">
          <div>
            <p>波特率</p>
            <strong class="proxy-mono">{{ proxy.baud }}</strong>
          </div>
          <div class="proxy-metric-bandwidth">
            <div>
              <p :class="{ danger: proxy.status === 'error' }">实时带宽</p>
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
            <span class="proxy-toggle">
              <input type="checkbox" :checked="proxy.active" />
              <span></span>
            </span>
            <span class="proxy-toggle-text">{{ proxy.toggleLabel }}</span>
          </label>
          <div class="proxy-footer-actions">
            <button class="icon-btn" type="button" title="抓包" @click="openCaptureModal(proxy)">
              <span class="material-symbols-outlined">terminal</span>
            </button>
            <button class="icon-btn" type="button" title="编辑" @click="openEditModal(proxy)">
              <span class="material-symbols-outlined">edit</span>
            </button>
            <button class="icon-btn danger" type="button" title="删除">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </div>
        </div>
      </article>
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
            <h2>编辑转发代理</h2>
          </div>
          <button class="proxy-modal-close" type="button" @click="closeModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="proxy-modal-body">
          <div class="proxy-modal-stack">
            <div class="proxy-modal-grid">
              <div class="proxy-field">
                <label>代理名称</label>
                <input type="text" v-model="proxyName" />
              </div>
              <div class="proxy-field">
                <label>连接模式</label>
                <DropdownSelect v-model="connectionMode" class="proxy-select" :options="connectionOptions" />
              </div>
            </div>
            <div class="proxy-port-map">
              <div class="proxy-field">
                <label>
                  <span class="material-symbols-outlined">computer</span>
                  主机端口
                </label>
                <DropdownSelect v-model="hostPort" class="proxy-select" :options="portOptions" />
              </div>
              <div class="proxy-field">
                <label>
                  <span class="material-symbols-outlined">settings_input_component</span>
                  设备端口
                </label>
                <DropdownSelect v-model="devicePort" class="proxy-select" :options="portOptions" />
              </div>
            </div>
            <div class="proxy-section">
              <div class="proxy-section-title">
                <span class="material-symbols-outlined">settings_ethernet</span>
                串口参数配置
                <span>（两端需一致）</span>
              </div>
              <div class="proxy-section-grid">
                <div class="proxy-field">
                  <label>波特率</label>
                  <DropdownSelect v-model="baudRate" class="proxy-select" :options="baudOptions" />
                </div>
                <div class="proxy-field">
                  <label>数据位</label>
                  <div class="proxy-segmented">
                    <button type="button">5</button>
                    <button type="button">6</button>
                    <button type="button">7</button>
                    <button type="button" class="active">8</button>
                  </div>
                </div>
                <div class="proxy-field">
                  <label>校验位</label>
                  <DropdownSelect v-model="parity" class="proxy-select" :options="parityOptions" />
                </div>
                <div class="proxy-field">
                  <label>停止位</label>
                  <div class="proxy-segmented">
                    <button type="button" class="active">1</button>
                    <button type="button">1.5</button>
                    <button type="button">2</button>
                  </div>
                </div>
                <div class="proxy-field proxy-span-2">
                  <label>流控</label>
                  <div class="proxy-segmented">
                    <button type="button" class="active">None</button>
                    <button type="button">RTS/CTS</button>
                    <button type="button">XON/XOFF</button>
                  </div>
                </div>
              </div>
            </div>
            <div class="proxy-section proxy-modal-advanced">
              <div class="proxy-section-title muted">
                <span class="material-symbols-outlined">settings_suggest</span>
                高级选项
              </div>
              <div class="proxy-toggle-row">
                <label>
                  <span class="proxy-toggle">
                    <input type="checkbox" checked />
                    <span></span>
                  </span>
                  自动重连
                </label>
                <label>
                  <span class="proxy-toggle">
                    <input type="checkbox" />
                    <span></span>
                  </span>
                  详细日志
                </label>
              </div>
            </div>
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
              <h1 class="text-sm font-bold text-slate-900 leading-none">多协议通用报文分析引擎</h1>
              <div class="flex items-center gap-2 mt-1">
                <span class="flex h-2 w-2 rounded-full bg-emerald-500"></span>
                <p class="text-[10px] font-medium text-slate-500">
                  活动通道: {{ captureProxy ? captureProxy.hostPort : captureMeta.channel }} | 引擎状态: {{ captureMeta.engine }}
                </p>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="flex items-center bg-slate-100 rounded-md px-2 border border-slate-200">
              <span class="material-symbols-outlined text-slate-400">search</span>
              <input
                class="bg-transparent border-none text-xs w-64 lg:w-96 focus:ring-0 text-slate-900 placeholder-slate-500"
                placeholder="搜索标识、十六进制、协议、原始数据..."
                type="text"
              />
            </div>
            <div class="h-6 w-[1px] bg-slate-200 mx-1"></div>
            <button class="flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-bold transition-colors shadow-sm">
              <span class="material-symbols-outlined !text-sm">play_arrow</span> 继续捕获
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
                    <th class="px-3 py-2 border-b border-slate-200 w-16">序号</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-28">时间戳</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-12 text-center">方向</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-32">协议</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-16">长度</th>
                    <th class="px-3 py-2 border-b border-slate-200 w-72">原始数据</th>
                    <th class="px-3 py-2 border-b border-slate-200">摘要 (解析结果/HEX/ASCII)</th>
                  </tr>
                </thead>
                <tbody class="text-xs">
                  <tr
                    v-for="(frame, index) in filteredFrames"
                    :key="frame.id"
                    class="hover:bg-slate-50 cursor-pointer border-b border-slate-100"
                    :class="{ 'bg-orange-50/40 border-l-4 border-l-orange-400': frame.tone === 'red' }"
                    @click="selectFrame(frame)"
                  >
                    <td class="px-3 py-2 text-slate-400 font-mono">{{ 50234 - index }}</td>
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
                          <span>{{ frame.protocolLabel || (frame.tone === 'red' ? 'Unknown' : selectedProtocol) }}</span>
                        </div>
                        <div class="protocol-tooltip bg-slate-800 text-white text-[10px] px-2 py-1 rounded shadow-lg pointer-events-none whitespace-nowrap border border-slate-700">
                          {{ frame.protocolTooltip || (frame.tone === 'red' ? '未知协议 - 点击配置' : 'Modbus RTU v1.1') }}
                        </div>
                      </div>
                    </td>
                    <td class="px-3 py-2 text-slate-500">{{ frame.size }}B</td>
                    <td class="px-3 py-2 hex-font text-slate-400 truncate max-w-[240px]">{{ frame.note }}</td>
                    <td class="px-3 py-2 text-slate-600 italic">
                      {{ frame.summaryText || frame.summary || ('HEX: ' + frame.note + ' | ASCII: ....') }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <aside class="flex-1 w-[450px] flex flex-col border-l border-slate-200 bg-slate-50">
            <div class="px-4 py-3 border-b border-slate-200 flex justify-between items-center bg-white shadow-sm">
              <h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                <span class="material-symbols-outlined !text-sm text-blue-500">info</span> 报文解析详情
              </h2>
              <div class="flex gap-2">
                <button class="p-1 hover:bg-slate-100 rounded" title="复制原始十六进制">
                  <span class="material-symbols-outlined !text-sm">content_copy</span>
                </button>
                <button class="p-1 hover:bg-slate-100 rounded" @click="closeCaptureModal">
                  <span class="material-symbols-outlined !text-sm">close</span>
                </button>
              </div>
            </div>
            <div class="flex-1 overflow-y-auto">
              <div class="p-6 text-center space-y-4 border-b border-slate-200 bg-orange-50/20">
                <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-orange-100 text-orange-600 mb-1">
                  <span class="material-symbols-outlined !text-3xl">question_mark</span>
                </div>
                <div>
                  <h3 class="text-sm font-bold text-slate-800">
                    {{ isUnknownFrame ? '未知协议报文 (Unknown Protocol)' : `${activeProtocolLabel} 报文` }}
                  </h3>
                  <p class="text-[11px] text-slate-500 mt-1 max-w-[280px] mx-auto leading-relaxed">
                    {{
                      isUnknownFrame
                        ? '系统未能自动匹配已知的解析插件。您可以尝试手动配置解析规则，或使用万能解析脚本。'
                        : '已匹配协议解析插件，当前展示该报文的解析详情。'
                    }}
                  </p>
                </div>
                <div class="flex justify-center gap-3">
                  <button class="px-3 py-1.5 bg-white border border-slate-300 rounded text-[11px] font-bold hover:bg-slate-50 transition-colors shadow-sm">
                    {{ isUnknownFrame ? '手动解析' : '查看详情' }}
                  </button>
                  <button class="px-3 py-1.5 bg-blue-600 text-white rounded text-[11px] font-bold hover:bg-blue-700 transition-colors flex items-center gap-1 shadow-md">
                    <span class="material-symbols-outlined !text-xs">schema</span>
                    {{ isUnknownFrame ? '配置解析规则' : '调整解析规则' }}
                  </button>
                </div>
              </div>
              <div class="p-4 border-b border-slate-200">
                <div class="flex items-center justify-between mb-3">
                  <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">原始十六进制 (RAW HEX)</h3>
                  <span class="text-[10px] font-mono bg-slate-200 px-1.5 py-0.5 rounded text-slate-600">
                    {{ activeHexSize }} 字节
                  </span>
                </div>
                <div class="bg-white border border-slate-200 rounded-lg overflow-hidden flex shadow-inner">
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
              </div>
              <div class="p-4 space-y-4">
                <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">协议层级解析 (PROTOCOL TREE)</h3>
                <div class="relative pl-4 space-y-1">
                  <div class="flex items-center gap-2 -ml-4 cursor-pointer hover:bg-slate-100 p-1 rounded transition-colors group">
                    <span class="material-symbols-outlined text-slate-400 group-open:rotate-90">arrow_right</span>
                    <span class="text-[11px] font-bold text-slate-500 uppercase">链路层 (Data Link Layer)</span>
                  </div>
                  <div class="tree-line relative pl-2 space-y-1">
                    <details class="group" open>
                      <summary class="flex items-center gap-2 list-none cursor-pointer hover:bg-slate-100 p-1 rounded -ml-4 transition-colors">
                        <span class="material-symbols-outlined text-blue-500 group-open:rotate-90 transition-transform">arrow_drop_down</span>
                        <span class="text-[11px] font-bold text-slate-800 uppercase">Agnostic Data Frame</span>
                      </summary>
                      <div class="mt-2 space-y-0.5 pl-2">
                        <div class="grid grid-cols-12 text-[9px] font-bold text-slate-400 px-2 py-1 uppercase tracking-tighter">
                          <div class="col-span-3">原始值</div>
                          <div class="col-span-4">字段</div>
                          <div class="col-span-5 text-right">解析值</div>
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
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            </div>
            <div class="p-4 bg-slate-100/50 border-t border-slate-200">
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">实时网络指标</p>
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-white p-2 rounded border border-slate-200 shadow-sm">
                  <p class="text-[9px] text-slate-500">往返延时 (RTT)</p>
                  <p class="text-sm font-bold text-emerald-500">{{ captureMetrics.rtt }}</p>
                </div>
                <div class="bg-white p-2 rounded border border-slate-200 shadow-sm">
                  <p class="text-[9px] text-slate-500">丢包率 (Packet Loss)</p>
                  <p class="text-sm font-bold text-slate-900">{{ captureMetrics.loss }}</p>
                </div>
              </div>
            </div>
          </aside>
        </main>
        <footer class="px-4 py-2 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div class="flex items-center gap-6">
            <div class="flex items-center gap-2">
              <span class="text-[10px] font-bold text-slate-500 uppercase">接收缓冲区</span>
              <div class="w-32 h-2 bg-slate-200 rounded-full overflow-hidden border border-slate-300">
                <div class="h-full bg-amber-500" :style="{ width: `${captureMeta.bufferUsed}%` }"></div>
              </div>
              <span class="text-[10px] font-mono font-bold text-slate-600">{{ captureMeta.bufferUsed }}%</span>
            </div>
            <div class="h-4 w-[1px] bg-slate-300"></div>
            <p class="text-[10px] font-medium text-slate-500 uppercase">
              显示 {{ captureMeta.rangeStart }}-{{ captureMeta.rangeEnd }} / 共 {{ captureMeta.totalFrames }} 报文
            </p>
          </div>
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-1 bg-white p-0.5 rounded border border-slate-200">
              <button class="p-1 hover:bg-slate-100 rounded" disabled>
                <span class="material-symbols-outlined !text-sm">first_page</span>
              </button>
              <button class="p-1 hover:bg-slate-100 rounded">
                <span class="material-symbols-outlined !text-sm">chevron_left</span>
              </button>
              <div class="px-3 text-[10px] font-bold text-slate-700">第 {{ captureMeta.page }} / {{ captureMeta.pageCount }} 页</div>
              <button class="p-1 hover:bg-slate-100 rounded">
                <span class="material-symbols-outlined !text-sm">chevron_right</span>
              </button>
              <button class="p-1 hover:bg-slate-100 rounded">
                <span class="material-symbols-outlined !text-sm">last_page</span>
              </button>
            </div>
            <button class="flex items-center gap-1 px-3 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded text-[10px] font-bold transition-colors">
              <span class="material-symbols-outlined !text-sm">download</span> 导出分析结果
            </button>
          </div>
        </footer>
      </div>
    </div>
  </teleport>
</template>
