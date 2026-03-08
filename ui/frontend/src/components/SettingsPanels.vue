<script setup>
import { inject } from 'vue'
import DropdownSelect from './DropdownSelect.vue'

const t = inject('t', (key) => key)
const tr = inject('tr', (text) => text)

defineProps({
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
  'update:uiLanguage',
  'update:uiTheme',
  'update:autoConnectOnStart',
])
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
        <label class="file-row">
          {{ t('settings.workspace') }}
          <div class="file-input">
            <span class="material-symbols-outlined">folder_open</span>
            <input :value="dslWorkspacePath" type="text" readonly />
          </div>
          <button class="btn btn-outline" type="button" @click="emit('choose-dsl-workspace')">{{ t('settings.chooseFolder') }}</button>
        </label>
        <div class="divider"></div>
        <div class="panel-title simple inline">
          {{ t('settings.plugins.title') }}
          <button
            class="link-btn"
            type="button"
            disabled
            :title="tr('鎻掍欢甯傚満鍒锋柊鑳藉姏灏嗗湪鍚庣画鐗堟湰鎻愪緵')"
          >
            <span class="material-symbols-outlined">refresh</span>
            {{ t('settings.plugins.refresh') }}
          </button>
        </div>
        <div class="plugin-list">
          <div class="plugin-item">
            <div>
              <div class="plugin-title">Modbus TCP/RTU</div>
              <div class="plugin-meta">{{ tr('v1.2.4 - 已启用') }}</div>
            </div>
            <span class="badge badge-green">{{ tr('已启用') }}</span>
          </div>
          <div class="plugin-item muted">
            <div>
              <div class="plugin-title">{{ tr('MQTT 适配器') }}</div>
              <div class="plugin-meta">{{ tr('v0.9.8 - 未安装') }}</div>
            </div>
            <span class="badge badge-gray">{{ tr('未安装') }}</span>
          </div>
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

      <div v-if="settingsTab === 'runtime'" class="panel">
        <div class="panel-title simple">
          <span class="material-symbols-outlined">tune</span>{{ t('settings.tab.runtime') }}
        </div>
        <div class="empty-state muted">
          {{ tr('暂无可配置项，运行时设置将随着模块扩展开放。') }}
        </div>
      </div>

      <div v-if="settingsTab === 'logs'" class="panel">
        <div class="panel-title simple">
          <span class="material-symbols-outlined">folder_open</span>{{ t('settings.tab.logs') }}
        </div>
        <div class="empty-state muted">
          {{ tr('日志采集与归档策略将在后续版本中提供。') }}
        </div>
      </div>
    </div>
  </div>
</template>
