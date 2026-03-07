<script setup>
import { inject } from 'vue'

const tr = inject('tr', (text) => text)

defineProps({
  proxy: {
    type: Object,
    required: true,
  },
  statusLabel: {
    type: String,
    default: '',
  },
  routeLabel: {
    type: String,
    default: '',
  },
  toggleLabel: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['capture', 'edit', 'delete', 'retry', 'toggle'])
</script>

<template>
  <article class="proxy-panel" :class="`status-${proxy.status}`">
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
        {{ statusLabel }}
      </span>
    </div>

    <div class="proxy-route-card" :class="`status-${proxy.status}`">
      <div class="proxy-route-col">
        <p>{{ tr('主机源端口') }}</p>
        <span class="proxy-route-chip proxy-mono">{{ proxy.hostPort }}</span>
      </div>
      <div class="proxy-route-state" :class="proxy.routeTone">
        <span class="material-symbols-outlined">{{ proxy.routeIcon }}</span>
        <span>{{ routeLabel }}</span>
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
      <button class="proxy-error-retry" type="button" @click="emit('retry', proxy)">
        <span class="material-symbols-outlined">refresh</span>
        {{ tr('重试') }}
      </button>
    </div>

    <div class="proxy-panel-footer" :class="`status-${proxy.status}`">
      <label class="proxy-footer-toggle">
        <span class="proxy-toggle" :class="{ active: proxy.active }" @click="emit('toggle', { proxy, active: !proxy.active })">
          <span class="proxy-toggle-track"></span>
        </span>
        <span class="proxy-toggle-text">{{ toggleLabel }}</span>
      </label>
      <div class="proxy-footer-actions">
        <button class="icon-btn" type="button" :title="tr('抓包')" @click="emit('capture', proxy)">
          <span class="material-symbols-outlined">terminal</span>
        </button>
        <button class="icon-btn" type="button" :title="tr('编辑')" @click="emit('edit', proxy)">
          <span class="material-symbols-outlined">edit</span>
        </button>
        <button class="icon-btn danger" type="button" :title="tr('删除')" @click="emit('delete', proxy)">
          <span class="material-symbols-outlined">delete</span>
        </button>
      </div>
    </div>
  </article>
</template>
