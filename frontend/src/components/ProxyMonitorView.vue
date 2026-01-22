<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import DropdownSelect from './DropdownSelect.vue'

const filterTabs = [
  { id: 'all', label: '全部转发' },
  { id: 'running', label: '运行中' },
  { id: 'stopped', label: '已停止' },
  { id: 'error', label: '异常' },
]
const activeFilter = ref(filterTabs[0].id)
const modalOpen = ref(false)
const modalProxy = ref(null)
const proxyName = ref('')
const connectionMode = ref('透传模式')
const hostPort = ref('COM3')
const devicePort = ref('COM5')
const baudRate = ref('115200')
const parity = ref('None (无)')

const connectionOptions = ['透传模式', '协议转换', '映射模式']
const portOptions = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM10', 'COM12']
const baudOptions = ['4800', '9600', '19200', '38400', '57600', '115200']
const parityOptions = ['None (无)', 'Even (偶)', 'Odd (奇)', 'Mark', 'Space']

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
    name: '电机反馈集线器',
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

function openEditModal(proxy) {
  console.debug('[proxy-monitor] openEditModal', proxy && proxy.id ? proxy.id : proxy)
  modalProxy.value = proxy
  proxyName.value = proxy && proxy.name ? proxy.name : ''
  hostPort.value = proxy && proxy.hostPort ? proxy.hostPort : hostPort.value
  devicePort.value = proxy && proxy.devicePort ? proxy.devicePort : devicePort.value
  baudRate.value = proxy && proxy.baud ? String(proxy.baud) : baudRate.value
  modalOpen.value = true
}

function closeModal(event) {
  const target = event && event.target ? event.target.tagName || event.target.className : 'unknown'
  console.debug('[proxy-monitor] closeModal', target, new Error().stack)
  modalOpen.value = false
}

watch(
  () => modalOpen.value,
  (open) => {
    console.debug('[proxy-monitor] modalOpen changed', open)
    document.body.classList.toggle('proxy-edit-open', open)
  }
)

onBeforeUnmount(() => {
  document.body.classList.remove('proxy-edit-open')
})
</script>

<template>
  <section class="page proxy-page proxy-dashboard">
    <header class="proxy-dashboard-hero">
      <div class="proxy-hero-card">
        <div>
          <h2>串口代理转发监控</h2>
          <p>管理串口转发对并实时监控数据流状态。</p>
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
            <button class="icon-btn" type="button" title="终端">
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
          <p>将物理串口连接到虚拟代理节点</p>
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
                  主机源端口
                </label>
                <DropdownSelect v-model="hostPort" class="proxy-select" :options="portOptions" />
              </div>
              <div class="proxy-field">
                <label>
                  <span class="material-symbols-outlined">settings_input_component</span>
                  设备代理端口
                </label>
                <DropdownSelect v-model="devicePort" class="proxy-select" :options="portOptions" />
              </div>
            </div>

            <div class="proxy-section">
              <div class="proxy-section-title">
                <span class="material-symbols-outlined">settings_ethernet</span>
                串口参数配置
                <span>（两端同步应用）</span>
              </div>
              <div class="proxy-section-grid">
                <div class="proxy-field">
                  <label>波特率 (Baud Rate)</label>
                  <DropdownSelect v-model="baudRate" class="proxy-select" :options="baudOptions" />
                </div>
                <div class="proxy-field">
                  <label>数据位 (Data Bits)</label>
                  <div class="proxy-segmented">
                    <button type="button">5</button>
                    <button type="button">6</button>
                    <button type="button">7</button>
                    <button type="button" class="active">8</button>
                  </div>
                </div>
                <div class="proxy-field">
                  <label>校验位 (Parity)</label>
                  <DropdownSelect v-model="parity" class="proxy-select" :options="parityOptions" />
                </div>
                <div class="proxy-field">
                  <label>停止位 (Stop Bits)</label>
                  <div class="proxy-segmented">
                    <button type="button" class="active">1</button>
                    <button type="button">1.5</button>
                    <button type="button">2</button>
                  </div>
                </div>
                <div class="proxy-field proxy-span-2">
                  <label>流控 (Flow Control)</label>
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
                高级运行选项
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
                  详细日志记录
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>
