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
const selectedFrame = ref(null)

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
    name: '电机反馈转发器',
    meta: 'ID: PX-00992 · 8-E-1',
    status: 'stopped',
    statusLabel: '已停止',
    statusIcon: 'pause_circle',
    routeIcon: 'more_horiz',
    routeLabel: '空闲',
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
    name: 'GPS 数据流',
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

const captureFrames = ref([
  {
    id: 'frame-001',
    direction: 'RX',
    time: '12:41:03.482',
    size: 64,
    note: '握手：READY',
    summary: 'ACK 0x06',
    tone: 'green',
    warn: false,
    channel: 'COM5',
    baud: '115200',
  },
  {
    id: 'frame-002',
    direction: 'TX',
    time: '12:41:03.940',
    size: 128,
    note: 'XMODEM 块 #12',
    summary: 'Payload: 128 bytes',
    tone: 'blue',
    warn: false,
    channel: 'COM3',
    baud: '115200',
  },
  {
    id: 'frame-003',
    direction: 'RX',
    time: '12:41:04.102',
    size: 1,
    note: '重试信号',
    summary: 'NAK 0x15',
    tone: 'amber',
    warn: true,
    channel: 'COM5',
    baud: '115200',
  },
  {
    id: 'frame-004',
    direction: 'RX',
    time: '12:41:04.288',
    size: 0,
    note: '超时',
    summary: 'No response',
    tone: 'red',
    warn: true,
    channel: 'COM5',
    baud: '115200',
  },
])

const filteredFrames = computed(() => {
  if (captureFilter.value === 'all') return captureFrames.value
  if (captureFilter.value === 'error') {
    return captureFrames.value.filter((frame) => frame.tone === 'red')
  }
  return captureFrames.value.filter((frame) => frame.direction === captureFilter.value)
})

const captureStats = computed(() => {
  const frames = captureFrames.value
  const total = frames.length
  const rx = frames.filter((frame) => frame.direction === 'RX').length
  const tx = frames.filter((frame) => frame.direction === 'TX').length
  const errors = frames.filter((frame) => frame.tone === 'red').length
  return { total, rx, tx, errors }
})

function openEditModal(proxy) {
  console.debug('[proxy-monitor] openEditModal', proxy && proxy.id ? proxy.id : proxy)
  modalProxy.value = proxy
  proxyName.value = proxy && proxy.name ? proxy.name : ''
  hostPort.value = proxy && proxy.hostPort ? proxy.hostPort : hostPort.value
  devicePort.value = proxy && proxy.devicePort ? proxy.devicePort : devicePort.value
  baudRate.value = proxy && proxy.baud ? String(proxy.baud) : baudRate.value
  modalOpen.value = true
}

function openCaptureModal(proxy) {
  console.debug('[proxy-monitor] openCaptureModal', proxy && proxy.id ? proxy.id : proxy)
  captureProxy.value = proxy
  captureFilter.value = 'all'
  selectedFrame.value = captureFrames.value[0] || null
  captureOpen.value = true
}

function closeModal(event) {
  const target = event && event.target ? event.target.tagName || event.target.className : 'unknown'
  console.debug('[proxy-monitor] closeModal', target, new Error().stack)
  modalOpen.value = false
}

function closeCaptureModal(event) {
  const target = event && event.target ? event.target.tagName || event.target.className : 'unknown'
  console.debug('[proxy-monitor] closeCaptureModal', target, new Error().stack)
  captureOpen.value = false
}

function selectFrame(frame) {
  selectedFrame.value = frame
}

watch(
  () => modalOpen.value,
  (open) => {
    console.debug('[proxy-monitor] modalOpen changed', open)
    document.body.classList.toggle('proxy-edit-open', open)
  }
)

watch(
  () => captureOpen.value,
  (open) => {
    console.debug('[proxy-monitor] captureOpen changed', open)
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
          <p>管理转发链路并实时观察通信流量。</p>
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
            <p>主机端口</p>
            <span class="proxy-route-chip proxy-mono">{{ proxy.hostPort }}</span>
          </div>
          <div class="proxy-route-state" :class="proxy.routeTone">
            <span class="material-symbols-outlined">{{ proxy.routeIcon }}</span>
            <span>{{ proxy.routeLabel }}</span>
          </div>
          <div class="proxy-route-col">
            <p>设备端口</p>
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

      <button class="proxy-panel proxy-panel-add" type="button">
        <div class="proxy-add-icon">
          <span class="material-symbols-outlined">add</span>
        </div>
        <div class="proxy-add-copy">
          <h3>添加新转发代理</h3>
          <p>将物理串口连接到虚拟代理节点。</p>
        </div>
        <div class="proxy-add-tags">
          <span>RS-232</span>
          <span>RS-485</span>
          <span>USB-TTY</span>
        </div>
      </button>
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
                <DropdownSelect
                  v-model="connectionMode"
                  class="proxy-select"
                  :options="connectionOptions"
                />
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

    <div v-if="captureOpen" class="proxy-modal-overlay" @mousedown.self="closeCaptureModal">
      <div class="proxy-modal" @mousedown.stop @click.stop>
        <div class="proxy-modal-header">
          <div class="proxy-modal-title">
            <div class="proxy-modal-icon">
              <span class="material-symbols-outlined">monitoring</span>
            </div>
            <div>
              <h2>抓包详情</h2>
              <p class="proxy-subtitle">{{ captureProxy ? captureProxy.name : '代理会话' }}</p>
            </div>
          </div>
          <button class="proxy-modal-close" type="button" @click="closeCaptureModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="proxy-modal-body">
          <div class="proxy-modal-stream">
            <div class="proxy-modal-toolbar">
              <div class="proxy-modal-toolbar-left">
                <span>抓包</span>
                <div class="proxy-modal-toggle">
                  <button
                    type="button"
                    :class="{ active: captureFilter === 'all' }"
                    @click="captureFilter = 'all'"
                  >
                    全部
                  </button>
                  <button
                    type="button"
                    :class="{ active: captureFilter === 'RX' }"
                    @click="captureFilter = 'RX'"
                  >
                    RX
                  </button>
                  <button
                    type="button"
                    :class="{ active: captureFilter === 'TX' }"
                    @click="captureFilter = 'TX'"
                  >
                    TX
                  </button>
                  <button
                    type="button"
                    :class="{ active: captureFilter === 'error' }"
                    @click="captureFilter = 'error'"
                  >
                    异常
                  </button>
                </div>
              </div>
              <div class="proxy-modal-toolbar-right">
                <span>{{ filteredFrames.length }} 条</span>
              </div>
            </div>

            <div class="proxy-modal-list">
              <div class="proxy-modal-list-header">
                <span>方向</span>
                <span>负载</span>
                <span>摘要</span>
              </div>
              <div
                v-for="frame in filteredFrames"
                :key="frame.id"
                class="proxy-frame"
                :class="{ error: frame.tone === 'red' }"
              >
                <div class="proxy-frame-row" @click="selectFrame(frame)">
                  <span
                    class="proxy-chip"
                    :class="[
                      frame.tone === 'red'
                        ? 'tone-red'
                        : frame.direction === 'RX'
                        ? 'tone-green'
                        : frame.tone === 'amber'
                        ? 'tone-amber'
                        : 'tone-blue',
                    ]"
                    :data-warn="frame.warn"
                  >
                    {{ frame.direction }}
                  </span>
                  <div class="note">
                    <div>{{ frame.note }}</div>
                    <div class="proxy-mono">{{ frame.time }}</div>
                  </div>
                  <div class="col-summary" :class="{ error: frame.tone === 'red' }">
                    {{ frame.summary }}
                  </div>
                </div>
                <div v-if="selectedFrame && selectedFrame.id === frame.id" class="proxy-frame-detail">
                  <div class="proxy-detail-row">
                    <span>大小</span>
                    <strong class="proxy-mono">{{ frame.size }} bytes</strong>
                  </div>
                  <div class="proxy-detail-row">
                    <span>通道</span>
                    <strong class="proxy-mono">{{ frame.channel }}</strong>
                  </div>
                  <div class="proxy-detail-row">
                    <span>波特率</span>
                    <strong class="proxy-mono">{{ frame.baud }}</strong>
                  </div>
                  <div class="proxy-detail-row">
                    <span>状态</span>
                    <strong
                      class="proxy-mono"
                      :class="frame.tone === 'red' ? 'tone-red' : frame.tone === 'amber' ? 'tone-amber' : 'tone-green'"
                    >
                      {{ frame.tone === 'red' ? '错误' : frame.tone === 'amber' ? '警告' : '正常' }}
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            <div class="proxy-modal-footer">
              <button class="proxy-btn ghost" type="button">清空</button>
              <div class="proxy-footer-actions">
                <button class="proxy-btn warning" type="button">暂停</button>
                <button class="proxy-btn primary" type="button">导出</button>
              </div>
            </div>
          </div>

          <aside class="proxy-modal-side">
            <div>
              <h4>会话统计</h4>
              <div class="proxy-stat-card">
                <span>总帧数</span>
                <div class="proxy-stat-value">
                  <strong>{{ captureStats.total }}</strong>
                  <em>实时</em>
                </div>
                <div class="proxy-stat-bar"></div>
              </div>
              <div class="proxy-stat-card">
                <span>异常</span>
                <div class="proxy-stat-value">
                  <strong class="danger">{{ captureStats.errors }}</strong>
                  <em>告警</em>
                </div>
                <div class="proxy-stat-bar"></div>
              </div>
            </div>
            <div class="proxy-side-block">
              <h5>方向</h5>
              <label>
                <input type="checkbox" checked />
                RX 帧 {{ captureStats.rx }}
              </label>
              <label>
                <input type="checkbox" checked />
                TX 帧 {{ captureStats.tx }}
              </label>
            </div>
            <div class="proxy-side-tip">
              <div class="proxy-side-tip-title">
                <span class="material-symbols-outlined">tips_and_updates</span>
                提示
              </div>
              当前为演示数据，可接入 bridge 事件展示真实帧。
            </div>
          </aside>
        </div>
      </div>
    </div>
  </teleport>
</template>
