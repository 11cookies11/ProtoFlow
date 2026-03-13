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
  skillRoots: {
    type: Array,
    default: () => [],
  },
  skillItems: {
    type: Array,
    default: () => [],
  },
  pluginsRefreshing: {
    type: Boolean,
    default: false,
  },
  skillsRefreshing: {
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
  'refresh-skills',
  'update:uiLanguage',
  'update:uiTheme',
  'update:autoConnectOnStart',
])

const pluginFilter = ref('all')
const protocolFilter = ref('all')
const selectedSkillId = ref('')

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

const normalizedSkillItems = computed(() => {
  if (!Array.isArray(props.skillItems)) return []
  return props.skillItems.map((item) => {
    const tags = Array.isArray(item?.tags) ? item.tags.map((tag) => String(tag)) : []
    const references = Array.isArray(item?.references) ? item.references.map((file) => String(file)) : []
    const examples = Array.isArray(item?.examples) ? item.examples.map((file) => String(file)) : []
    const files = Array.isArray(item?.files) ? item.files.map((file) => String(file)) : []
    return {
      id: String(item?.id || item?.name || ''),
      name: String(item?.name || item?.id || 'unknown'),
      version: String(item?.version || ''),
      summary: String(item?.summary || ''),
      description: String(item?.description || ''),
      type: String(item?.type || 'unknown'),
      category: String(item?.category || ''),
      tags,
      references,
      examples,
      files,
      instructionFile: String(item?.instruction_file || ''),
      instructionText: String(item?.instruction_text || ''),
      bundleRoot: String(item?.bundle_root || ''),
      manifestPath: String(item?.manifest_path || ''),
      sourcePath: String(item?.source_path || ''),
      meta: item?.version ? `v${item.version}` : tt('settings.meta.unversioned', '未标注版本'),
    }
  })
})

const selectedSkill = computed(() => {
  const items = normalizedSkillItems.value
  if (!items.length) return null
  const hit = items.find((item) => item.id === selectedSkillId.value)
  return hit || items[0]
})

const selectedInstructionPreview = computed(() => {
  const text = String(selectedSkill.value?.instructionText || '').trim()
  if (!text) return tt('settings.skills.noInstruction', '未找到 SKILL.md 内容')
  return text
})
</script>

<template>
  <div>
    <div class="tab-strip secondary">
      <button :class="{ active: settingsTab === 'general' }" @click="emit('set-tab', 'general')">{{ t('settings.tab.general') }}</button>
      <button :class="{ active: settingsTab === 'plugins' }" @click="emit('set-tab', 'plugins')">{{ t('settings.tab.plugins') }}</button>
      <button :class="{ active: settingsTab === 'skills' }" @click="emit('set-tab', 'skills')">{{ tt('settings.tab.skills', 'Skills') }}</button>
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

      <div v-if="settingsTab === 'skills'" class="panel">
        <div class="panel-title simple">
          <span class="material-symbols-outlined">smart_toy</span>{{ tt('settings.tab.skills', 'Skills') }}
        </div>

        <div class="panel-title simple inline">
          {{ tt('settings.skills.title', 'Skill Bundles') }}
          <button class="link-btn" type="button" :disabled="skillsRefreshing" @click="emit('refresh-skills')">
            <span class="material-symbols-outlined">refresh</span>
            {{ tt('settings.skills.refresh', '刷新列表') }}
          </button>
        </div>

        <div class="file-row">
          <span class="section-title">{{ tt('settings.skills.roots', 'Skill 目录') }}</span>
          <div class="file-row-controls">
            <div class="file-input">
              <span class="material-symbols-outlined">folder_open</span>
              <input :value="Array.isArray(skillRoots) && skillRoots.length ? skillRoots.join(' | ') : tt('settings.skills.noRoots', '未发现 skill 目录')" type="text" readonly />
            </div>
          </div>
        </div>

        <div v-if="normalizedSkillItems.length" class="settings-skill-grid">
          <div class="plugin-list">
            <button
              v-for="item in normalizedSkillItems"
              :key="item.id"
              class="plugin-item skill-item-button"
              :class="{ active: selectedSkill && selectedSkill.id === item.id }"
              type="button"
              @click="selectedSkillId = item.id"
            >
              <div>
                <div class="plugin-title">{{ item.name }}</div>
                <div class="plugin-meta">{{ item.meta }} · {{ item.type }}</div>
                <div class="plugin-meta">{{ item.summary || tt('settings.skills.noSummary', '暂无摘要') }}</div>
              </div>
              <span class="badge badge-blue">{{ tt('settings.filter.available', '可用') }}</span>
            </button>
          </div>

          <div v-if="selectedSkill" class="panel subtle">
            <div class="panel-title simple">{{ selectedSkill.name }}</div>
            <div class="skill-meta-grid">
              <div><strong>ID</strong><p>{{ selectedSkill.id }}</p></div>
              <div><strong>{{ tt('settings.skills.version', '版本') }}</strong><p>{{ selectedSkill.version || '--' }}</p></div>
              <div><strong>{{ tt('settings.skills.type', '类型') }}</strong><p>{{ selectedSkill.type || '--' }}</p></div>
              <div><strong>{{ tt('settings.skills.category', '分类') }}</strong><p>{{ selectedSkill.category || '--' }}</p></div>
            </div>

            <div class="skill-section">
              <strong>{{ tt('settings.skills.summary', '摘要') }}</strong>
              <p>{{ selectedSkill.summary || tt('settings.skills.noSummary', '暂无摘要') }}</p>
            </div>

            <div class="skill-section">
              <strong>{{ tt('settings.skills.description', '说明') }}</strong>
              <p>{{ selectedSkill.description || tt('settings.skills.noDescription', '暂无说明') }}</p>
            </div>

            <div class="skill-section">
              <strong>{{ tt('settings.skills.tags', '标签') }}</strong>
              <div class="chip-row">
                <span v-for="tag in selectedSkill.tags" :key="tag" class="badge badge-gray">{{ tag }}</span>
                <span v-if="!selectedSkill.tags.length" class="muted">{{ tt('settings.skills.noTags', '无标签') }}</span>
              </div>
            </div>

            <div class="skill-section">
              <strong>{{ tt('settings.skills.paths', '路径') }}</strong>
              <p>{{ selectedSkill.bundleRoot || '--' }}</p>
              <p>{{ selectedSkill.manifestPath || '--' }}</p>
              <p v-if="selectedSkill.sourcePath">{{ selectedSkill.sourcePath }}</p>
            </div>

            <div class="skill-section">
              <strong>{{ tt('settings.skills.references', 'References') }}</strong>
              <div class="chip-row">
                <span v-for="file in selectedSkill.references" :key="file" class="badge badge-gray">{{ file }}</span>
                <span v-if="!selectedSkill.references.length" class="muted">{{ tt('settings.skills.noReferences', '无 references') }}</span>
              </div>
            </div>

            <div class="skill-section">
              <strong>{{ tt('settings.skills.examples', 'Examples') }}</strong>
              <div class="chip-row">
                <span v-for="file in selectedSkill.examples" :key="file" class="badge badge-gray">{{ file }}</span>
                <span v-if="!selectedSkill.examples.length" class="muted">{{ tt('settings.skills.noExamples', '无 examples') }}</span>
              </div>
            </div>

            <div class="skill-section">
              <strong>{{ tt('settings.skills.instruction', 'SKILL.md') }}</strong>
              <pre class="skill-doc-preview">{{ selectedInstructionPreview }}</pre>
            </div>
          </div>
        </div>
        <div v-else class="empty-state muted">{{ tt('settings.skills.empty', '未发现可用 skill bundle') }}</div>
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

