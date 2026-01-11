<script setup>
import { computed, ref } from 'vue'

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
            <button class="icon-btn" type="button" title="Terminal">
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
</template>
