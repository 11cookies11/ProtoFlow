<script setup>
import { computed, inject, ref } from 'vue'
import DropdownSelect from './DropdownSelect.vue'

const t = inject('t', (key) => key)
const tt = (key, fallback) => t(key, fallback)

const props = defineProps({
  settingsTab: {
    type: String,
    default: 'general',
  },
  uiLanguage: {
    type: String,
    default: '',
  },
  uiTheme: {
    type: String,
    default: '',
  },
  autoConnectOnStart: {
    type: Boolean,
    default: false,
  },
  dslWorkspacePath: {
    type: String,
    default: '',
  },
  pluginDirectory: {
    type: String,
    default: '',
  },
  pluginItems: {
    type: Array,
    default: () => [],
  },
  protocolItems: {
    type: Array,
    default: () => [],
  },
  pluginsRefreshing: {
    type: Boolean,
    default: false,
  },
  languageOptions: {
    type: Array,
    default: () => [],
  },
  themeOptions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits([
  'set-tab',
  'choose-dsl-workspace',
  'refresh-plugins',
  'update:uiLanguage',
  'update:uiTheme',
  'update:autoConnectOnStart',
])

const pluginFilter = ref('all')
const protocolFilter = ref('all')

const normalizedPluginItems = computed(() => {
  if (!Array.isArray(props.pluginItems)) return []
  return props.pluginItems.map((item) => {
    const status = String(item?.status || 'available').toLowerCase()
    const isEnabled = status === 'enabled'
    const isError = status === 'error'
    return {
      id: String(item?.id || item?.name || ''),
      name: String(item?.name || item?.id || 'unknown'),
      version: String(item?.version || ''),
      status,
      statusLabel: isEnabled
        ? tt('settings.filter.enabled', '已启用')
        : isError
          ? tt('filter.error', '异常')
          : tt('settings.filter.available', '可用'),
      badgeClass: isEnabled ? 'badge-green' : isError ? 'badge-yellow' : 'badge-gray',
      meta: item?.version ? `v${item.version}` : tt('settings.meta.unversioned', '未标注版本'),
    }
  })
})

const filteredPluginItems = computed(() => {
  if (pluginFilter.value === 'all') return normalizedPluginItems.value
  return normalizedPluginItems.value.filter((item) => item.status === pluginFilter.value)
})

const normalizedProtocolItems = computed(() => {
  if (!Array.isArray(props.protocolItems)) return []
  return props.protocolItems.map((item) => {
    const version = String(item?.version || '')
    const rawCategory = String(item?.category || '')
    const normalizedCategory = rawCategory.startsWith('modbus')
      ? 'modbus'
      : rawCategory === 'tcp'
        ? 'tcp'
        : 'custom'
    return {
      id: String(item?.id || item?.key || item?.name || ''),
      name: String(item?.name || item?.id || item?.key || 'unknown'),
      meta: version ? `v${version}` : tt('settings.meta.unversioned', '未标注版本'),
      statusLabel: tt('settings.filter.available', '可用'),
      badgeClass: 'badge-blue',
      category: normalizedCategory,
    }
  })
})

const filteredProtocolItems = computed(() => {
  if (protocolFilter.value === 'all') return normalizedProtocolItems.value
  return normalizedProtocolItems.value.filter((item) => item.category === protocolFilter.value)
})
</script>

<template>
  <div>
    <div class="tab-strip secondary">
      <button :class="{ active: settingsTab === 'general' }" @click="emit('set-tab', 'general')">{{ t('settings.tab.general') }}</button>
      <button :class="{ active: settingsTab === 'plugins' }" @click="emit('set-tab', 'plugins')">{{ t('settings.tab.plugins') }}</button>
      <button :class="{ active: settingsTab === 'runtime' }" @click="emit('set-tab', 'runtime')">{{ t('settings.tab.runtime') }}</button>
      <button :class="{ active: settingsTab === 'logs' }" @click="emit('set-tab', 'logs')">{{ t('settings.tab.logs') }}</button>
    </div>
    <div class="settings-stack">
      <div v-if="settingsTab === 'general'" class="panel">
        <div class="panel-title simple">
          <span class="material-symbols-outlined">tune</span>{{ t('settings.tab.general') }}
        </div>
        <div class="form-grid">
          <label>
            {{ t('settings.language') }}
            <DropdownSelect
              :model-value="uiLanguage"
              :options="languageOptions"
              @update:model-value="emit('update:uiLanguage', $event)"
            />
          </label>
          <label>
            {{ t('settings.theme') }}
            <DropdownSelect
              :model-value="uiTheme"
              :options="themeOptions"
              @update:model-value="emit('update:uiTheme', $event)"
            />
          </label>
        </div>
        <div class="toggle-row spaced">
          <div>
            <strong>{{ t('settings.autoConnect.title') }}</strong>
            <p>{{ t('settings.autoConnect.desc') }}</p>
          </div>
          <label class="switch">
            <input
              :checked="autoConnectOnStart"
              type="checkbox"
              @change="emit('update:autoConnectOnStart', $event.target.checked)"
            />
            <span></span>
          </label>
        </div>
      </div>

      <div v-if="settingsTab === 'plugins'" class="panel">
        <div class="panel-title simple">
          <span class="material-symbols-outlined">extension</span>{{ t('settings.tab.plugins') }}
        </div>

        <div class="file-row">
          <span class="section-title">{{ t('settings.workspace') }}</span>
          <div class="file-row-controls">
            <div class="file-input">
              <span class="material-symbols-outlined">folder_open</span>
              <input :value="dslWorkspacePath" type="text" readonly />
            </div>
            <button class="btn btn-outline" type="button" @click="emit('choose-dsl-workspace')">{{ t('settings.chooseFolder') }}</button>
          </div>
        </div>

        <div class="file-row">
          <span class="section-title">{{ tt('settings.plugins.directory', '插件目录') }}</span>
          <div class="file-row-controls">
            <div class="file-input">
              <span class="material-symbols-outlined">folder_open</span>
              <input :value="pluginDirectory" type="text" readonly />
            </div>
          </div>
        </div>

        <div class="divider"></div>
        <div class="panel-title simple inline">
          {{ t('settings.plugins.title') }}
          <button class="link-btn" type="button" :disabled="pluginsRefreshing" @click="emit('refresh-plugins')">
            <span class="material-symbols-outlined">refresh</span>
            {{ t('settings.plugins.refresh') }}
          </button>
        </div>

        <div class="plugin-filters">
          <button :class="{ active: pluginFilter === 'all' }" @click="pluginFilter = 'all'">{{ tt('filter.all', '全部') }}</button>
          <button :class="{ active: pluginFilter === 'enabled' }" @click="pluginFilter = 'enabled'">{{ tt('settings.filter.enabled', '已启用') }}</button>
          <button :class="{ active: pluginFilter === 'available' }" @click="pluginFilter = 'available'">{{ tt('settings.filter.available', '可用') }}</button>
          <button :class="{ active: pluginFilter === 'error' }" @click="pluginFilter = 'error'">{{ tt('filter.error', '异常') }}</button>
        </div>

        <div v-if="filteredPluginItems.length" class="plugin-list">
          <div v-for="item in filteredPluginItems" :key="item.id" class="plugin-item">
            <div>
              <div class="plugin-title">{{ item.name }}</div>
              <div class="plugin-meta">{{ item.meta }}</div>
            </div>
            <span class="badge" :class="item.badgeClass">{{ item.statusLabel }}</span>
          </div>
        </div>
        <div v-else class="empty-state muted">{{ normalizedPluginItems.length ? tt('settings.empty.filtered', '当前筛选无结果') : tt('settings.empty.noPlugins', '未发现可用插件') }}</div>

        <div class="divider"></div>
        <div class="panel-title simple inline">
          {{ tt('settings.protocols.title', '协议包') }}
        </div>
        <div class="plugin-filters">
          <button :class="{ active: protocolFilter === 'all' }" @click="protocolFilter = 'all'">{{ tt('filter.all', '全部') }}</button>
          <button :class="{ active: protocolFilter === 'modbus' }" @click="protocolFilter = 'modbus'">Modbus</button>
          <button :class="{ active: protocolFilter === 'tcp' }" @click="protocolFilter = 'tcp'">TCP</button>
          <button :class="{ active: protocolFilter === 'custom' }" @click="protocolFilter = 'custom'">{{ tt('protocol.tab.custom', '自定义') }}</button>
        </div>
        <div v-if="filteredProtocolItems.length" class="plugin-list">
          <div v-for="item in filteredProtocolItems" :key="item.id" class="plugin-item">
            <div>
              <div class="plugin-title">{{ item.name }}</div>
              <div class="plugin-meta">{{ item.meta }}</div>
            </div>
            <span class="badge" :class="item.badgeClass">{{ item.statusLabel }}</span>
          </div>
        </div>
        <div v-else class="empty-state muted">{{ normalizedProtocolItems.length ? tt('settings.empty.filtered', '当前筛选无结果') : tt('settings.empty.noProtocols', '未发现可用协议包') }}</div>

      </div>

      <div v-if="settingsTab === 'runtime'" class="panel">
        <div class="panel-title simple">
          <span class="material-symbols-outlined">tune</span>{{ t('settings.tab.runtime') }}
        </div>
        <div class="empty-state muted">
          {{ tt('settings.runtime.placeholder', '暂无可配置项，运行时设置将随着模块扩展开放。') }}
        </div>
      </div>

      <div v-if="settingsTab === 'logs'" class="panel">
        <div class="panel-title simple">
          <span class="material-symbols-outlined">folder_open</span>{{ t('settings.tab.logs') }}
        </div>
        <div class="empty-state muted">
          {{ tt('settings.logs.placeholder', '日志采集与归档策略将在后续版本中提供。') }}
        </div>
      </div>
    </div>
  </div>
</template>

