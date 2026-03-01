<script setup>
import { inject } from 'vue'

const t = inject('t', (key) => key)
const tr = inject('tr', (text) => text)

defineProps({
  protocolTab: {
    type: String,
    default: 'all',
  },
  filteredProtocolCards: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['set-tab', 'create', 'details', 'delete'])
</script>

<template>
  <div>
    <div class="tab-strip secondary">
      <button :class="{ active: protocolTab === 'all' }" @click="emit('set-tab', 'all')">{{ t('protocol.tab.all') }}</button>
      <button :class="{ active: protocolTab === 'modbus' }" @click="emit('set-tab', 'modbus')">Modbus</button>
      <button :class="{ active: protocolTab === 'tcp' }" @click="emit('set-tab', 'tcp')">TCP/IP</button>
      <button :class="{ active: protocolTab === 'custom' }" @click="emit('set-tab', 'custom')">{{ t('protocol.tab.custom') }}</button>
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
          <button class="btn btn-ghost" @click="emit('details', card)">
            {{ card.source === 'custom' ? tr('配置') : tr('查看') }}
          </button>
          <button v-if="card.source === 'custom'" class="icon-btn" @click="emit('delete', card)">
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
        <button class="btn btn-primary" @click="emit('create')">
          <span class="material-symbols-outlined">add</span>
          {{ t('action.createProtocol') }}
        </button>
      </div>
    </div>
  </div>
</template>
