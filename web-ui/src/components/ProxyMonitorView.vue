<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const filterTabs = ['全部代理', '正在运行', '已停止', '异常']
const activeFilter = ref(filterTabs[0])

const proxies = ref([
  {
    id: 'proxy-com3',
    name: 'COM3 - Sensor Node A',
    subtitle: '8-N-1 · 异步串行',
    status: 'running',
    statusLabel: 'RUNNING',
    baud: '115200',
    bandwidth: '12.4 KB/s',
    spark: 'M0 35 L 10 35 L 10 10 L 25 10 L 25 35 L 40 35 L 40 5 L 55 5 L 55 35 L 70 35 L 70 15 L 85 15 L 85 35 L 100 35',
    active: true,
    toggleLabel: 'Active',
  },
  {
    id: 'proxy-com7',
    name: 'COM7 - Motor Controller',
    subtitle: '8-E-1 · RS-485',
    status: 'stopped',
    statusLabel: 'STOPPED',
    baud: '9600',
    bandwidth: '0.0 KB/s',
    spark: 'M0 35 L 100 35',
    active: false,
    toggleLabel: 'Inactive',
  },
  {
    id: 'proxy-com1',
    name: 'COM1 - GPS Module',
    subtitle: '7-N-2 · NMEA-0183',
    status: 'error',
    statusLabel: 'ERROR',
    baud: '4800',
    bandwidth: '0.4 KB/s',
    spark: 'M0 35 L 5 35 L 5 10 L 10 10 L 10 35 L 15 35 L 15 10 L 20 10 L 20 35 L 90 35 L 90 5 L 95 5 L 95 35 L 100 35',
    active: true,
    toggleLabel: 'Faulty',
  },
])

const modalOpen = ref(false)
const modalProxy = ref(null)

const modalTitle = computed(() => {
  if (!modalProxy.value) return '抓包详情'
  return `抓包详情 - ${modalProxy.value.name}`
})

const filteredProxies = computed(() => {
  if (activeFilter.value === '全部代理') return proxies.value
  if (activeFilter.value === '正在运行') {
    return proxies.value.filter((proxy) => proxy.status === 'running')
  }
  if (activeFilter.value === '已停止') {
    return proxies.value.filter((proxy) => proxy.status === 'stopped')
  }
  if (activeFilter.value === '异常') {
    return proxies.value.filter((proxy) => proxy.status === 'error')
  }
  return proxies.value
})

const protocolFrames = ref([
  {
    id: 'frame-1',
    time: '14:20:01.2',
    summary: 'Read Hold Regs',
    chips: [
      { text: '01', tone: 'amber', title: 'Slave Addr' },
      { text: '03', tone: 'blue', title: 'Function Code' },
      { text: '00 00 00 02', tone: 'green', title: 'Data Bytes' },
      { text: 'C4 0B', tone: 'rose', title: 'CRC Checksum' },
    ],
    detail: [
      { label: 'Slave Address:', value: '01 (1)', tone: 'amber' },
      { label: 'Function Code:', value: '03 (Read Holding Registers)', tone: 'blue' },
      { label: 'Start Address:', value: '0000 (0)' },
      { label: 'Quantity:', value: '0002 (2)' },
      { label: 'CRC:', value: '0x0BC4 [Valid]', tone: 'green' },
    ],
  },
  {
    id: 'frame-2',
    time: '14:20:01.5',
    summary: 'Resp: 50.0 / 70.0',
    chips: [
      { text: '01', tone: 'amber' },
      { text: '03', tone: 'blue' },
      { text: '04 01 F4 02 BC', tone: 'green' },
      { text: '9B 42', tone: 'rose' },
    ],
  },
  {
    id: 'frame-3',
    time: '14:20:02.8',
    summary: 'EXCEPTION: ILLEGAL_ADDR',
    error: true,
    chips: [
      { text: '01', tone: 'amber' },
      { text: '83', tone: 'red' },
      { text: '02', tone: 'green' },
      { text: 'FF FF', tone: 'rose', warn: true },
    ],
  },
  {
    id: 'frame-4',
    time: '14:20:03.2',
    note: 'Waiting for next frame...',
  },
])

function openModal(proxy) {
  modalProxy.value = proxy
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
}

watch(
  () => modalOpen.value,
  (open) => {
    document.body.classList.toggle('modal-open', open)
    document.body.classList.toggle('proxy-modal-open', open)
  }
)

onBeforeUnmount(() => {
  document.body.classList.remove('modal-open', 'proxy-modal-open')
})
</script>

<template>
  <section class="page proxy-page">
    <header class="page-header spaced proxy-hero">
      <div>
        <h2>代理监控</h2>
        <p>管理串口 COM 代理通道，监控物理层实时数据流与连接状态。</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" type="button">
          <span class="material-symbols-outlined">refresh</span>
          刷新状态
        </button>
        <button class="btn btn-primary" type="button">
          <span class="material-symbols-outlined">add</span>
          新增代理
        </button>
      </div>
    </header>

    <div class="proxy-filters">
      <button
        v-for="tab in filterTabs"
        :key="tab"
        class="proxy-filter"
        :class="{ active: activeFilter === tab }"
        type="button"
        @click="activeFilter = tab"
      >
        {{ tab }}
      </button>
    </div>

    <div class="proxy-grid">
      <article v-for="proxy in filteredProxies" :key="proxy.id" class="proxy-card">
        <div class="proxy-card-header">
          <div class="proxy-title">
            <div class="proxy-icon" :class="`accent-${proxy.status}`">
              <span class="material-symbols-outlined">settings_input_hdmi</span>
            </div>
            <div>
              <h3>{{ proxy.name }}</h3>
              <p class="proxy-subtitle">{{ proxy.subtitle }}</p>
            </div>
          </div>
          <span class="proxy-status" :class="proxy.status">
            <span class="dot"></span>
            {{ proxy.statusLabel }}
          </span>
        </div>

        <div class="proxy-card-body">
          <div class="proxy-metric">
            <span>波特率</span>
            <strong>{{ proxy.baud }}</strong>
          </div>
          <div class="proxy-metric">
            <span>实时带宽</span>
            <strong>{{ proxy.bandwidth }}</strong>
          </div>
          <div class="proxy-sparkline" :class="proxy.status">
            <svg viewBox="0 0 100 40" preserveAspectRatio="none">
              <path :d="proxy.spark" />
            </svg>
          </div>
        </div>

        <div class="proxy-card-footer">
          <div class="proxy-toggle-wrap">
            <label class="proxy-toggle">
              <input type="checkbox" :checked="proxy.active" />
              <span></span>
            </label>
            <span class="proxy-toggle-label">{{ proxy.toggleLabel }}</span>
          </div>
          <div class="proxy-actions">
            <button class="icon-btn" type="button" title="Terminal" @click="openModal(proxy)">
              <span class="material-symbols-outlined">terminal</span>
            </button>
            <button class="icon-btn" type="button" title="Edit">
              <span class="material-symbols-outlined">edit</span>
            </button>
            <button class="icon-btn" type="button" title="Delete">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </div>
        </div>
      </article>

      <button class="proxy-card proxy-card-add" type="button">
        <div class="proxy-add-icon">
          <span class="material-symbols-outlined">add</span>
        </div>
        <div class="proxy-add-title">添加 COM 监控节点</div>
        <div class="proxy-add-sub">支持 RS-232, RS-485 或 USB 转串口。</div>
      </button>
    </div>
  </section>

  <div v-if="modalOpen" class="proxy-modal-backdrop">
    <div class="proxy-modal">
      <div class="proxy-modal-header">
        <div class="proxy-modal-title">
          <div class="proxy-modal-icon">
            <span class="material-symbols-outlined">terminal</span>
          </div>
          <div>
            <h3>{{ modalTitle }}</h3>
            <div class="proxy-modal-meta">
              <span class="pulse-dot"></span>
              实时流量监控中 - 115200 bps
            </div>
          </div>
        </div>
        <div class="proxy-modal-actions">
          <div class="proxy-modal-select">
            <label>手动协议选择</label>
            <select>
              <option>Modbus RTU</option>
              <option>MQTT</option>
              <option>Raw Hex (无协议)</option>
              <option>Custom Protocol A</option>
            </select>
          </div>
          <button class="icon-btn" type="button" @click="closeModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </div>

      <div class="proxy-modal-body">
        <section class="proxy-modal-stream">
          <div class="proxy-modal-toolbar">
            <div class="proxy-modal-toolbar-left">
              <span class="material-symbols-outlined">filter_alt</span>
              <span>活动协议视图: Modbus RTU</span>
            </div>
            <div class="proxy-modal-toolbar-right">
              <span>右侧显示:</span>
              <div class="proxy-modal-toggle">
                <button type="button">ASCII</button>
                <button class="active" type="button">解析值</button>
              </div>
            </div>
          </div>

          <div class="proxy-modal-list">
            <div class="proxy-modal-list-header">
              <span class="col-time">时间戳</span>
              <span class="col-body">结构化协议字段(已对齐)</span>
              <span class="col-summary">解析摘要</span>
            </div>

            <div
              v-for="frame in protocolFrames"
              :key="frame.id"
              class="proxy-frame"
              :class="{ error: frame.error }"
            >
              <template v-if="frame.note">
                <span class="col-time">{{ frame.time }}</span>
                <span class="col-body note">{{ frame.note }}</span>
                <span class="col-summary"></span>
              </template>
              <template v-else>
                <div class="proxy-frame-row">
                  <span class="col-time">{{ frame.time }}</span>
                  <span class="col-body chips">
                    <span
                      v-for="chip in frame.chips"
                      :key="chip.text"
                      class="proxy-chip"
                      :class="`tone-${chip.tone}`"
                      :title="chip.title"
                      :data-warn="chip.warn ? 'true' : null"
                    >
                      {{ chip.text }}
                    </span>
                  </span>
                  <span class="col-summary" :class="{ error: frame.error }">{{ frame.summary }}</span>
                </div>
                <div v-if="frame.detail" class="proxy-frame-detail">
                  <div v-for="item in frame.detail" :key="item.label" class="proxy-detail-row">
                    <span>{{ item.label }}</span>
                    <span :class="item.tone ? `tone-${item.tone}` : ''">{{ item.value }}</span>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <div class="proxy-modal-footer">
            <div class="proxy-footer-actions">
              <button class="proxy-btn warning" type="button">
                <span class="material-symbols-outlined">pause</span>
                暂停
              </button>
              <button class="proxy-btn ghost" type="button">
                <span class="material-symbols-outlined">delete_sweep</span>
                重置
              </button>
            </div>
            <button class="proxy-btn primary" type="button">
              <span class="material-symbols-outlined">download</span>
              导出当前协议日志
            </button>
          </div>
        </section>

        <aside class="proxy-modal-side">
          <div>
            <h4>当前会话统计</h4>
            <div class="proxy-stat-card">
              <span>已处理帧数</span>
              <div class="proxy-stat-value">
                <strong>1,284</strong>
                <em>8.4 fps</em>
              </div>
              <div class="proxy-stat-bar"></div>
            </div>
            <div class="proxy-stat-card">
              <span>校验错误率</span>
              <div class="proxy-stat-value">
                <strong class="danger">0.08%</strong>
                <em>1 帧错误</em>
              </div>
            </div>
            <div class="proxy-stat-card">
              <span>持续监控时长</span>
              <div class="proxy-stat-value">
                <strong>00:42:15</strong>
              </div>
            </div>
          </div>

          <div class="proxy-side-block">
            <h5>视图过滤器</h5>
            <label>
              <input type="checkbox" checked />
              仅显示合法帧
            </label>
            <label>
              <input type="checkbox" />
              仅显示写指令
            </label>
          </div>

          <div class="proxy-side-tip">
            <div class="proxy-side-tip-title">
              <span class="material-symbols-outlined">info</span>
              当前配置
            </div>
            <p>Modbus RTU 监听中。解析对象 1-255 从站地址。</p>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>
