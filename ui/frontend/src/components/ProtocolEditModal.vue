<script setup>
import { inject } from 'vue'

const t = inject('t', (key) => key)
const tr = inject('tr', (text) => text)

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  mode: {
    type: String,
    default: 'create',
  },
  draft: {
    type: Object,
    default: () => ({}),
  },
  editing: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'save', 'update-draft'])

function updateDraft(field, value) {
  emit('update-draft', { field, value })
}
</script>

<template>
  <div v-if="open" class="modal-backdrop" @mousedown.self="emit('close')">
    <div class="channel-modal protocol-modal" @mousedown.stop @click.stop>
      <div class="modal-header">
        <div>
          <h3>{{ mode === 'create' ? tr('新建协议') : mode === 'edit' ? tr('配置协议') : tr('协议详情') }}</h3>
          <p>{{ mode === 'create' ? tr('添加自定义协议元数据，供解析引擎识别。') : tr('查看或更新协议描述与分类。') }}</p>
        </div>
        <button class="icon-btn" type="button" @click="emit('close')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="modal-body protocol-modal-body">
        <div class="form-grid protocol-grid">
          <label>
            {{ tr('协议名称') }}
            <input :value="draft.name" type="text" :disabled="mode === 'view'" @input="updateDraft('name', $event.target.value)" />
          </label>
          <label>
            {{ tr('键名') }}
            <input :value="draft.key" type="text" :disabled="mode !== 'create'" @input="updateDraft('key', $event.target.value)" />
          </label>
        </div>
        <div class="form-grid protocol-grid">
          <label>
            {{ tr('分类') }}
            <select :value="draft.category" :disabled="mode === 'view'" @change="updateDraft('category', $event.target.value)">
              <option value="modbus">Modbus</option>
              <option value="tcp">TCP/IP</option>
              <option value="custom">{{ t('protocol.tab.custom') }}</option>
            </select>
          </label>
          <label>
            {{ tr('状态') }}
            <select :value="draft.status" :disabled="mode === 'view'" @change="updateDraft('status', $event.target.value)">
              <option value="available">{{ tr('可用') }}</option>
              <option value="custom">{{ t('protocol.tab.custom') }}</option>
              <option value="disabled">{{ tr('已禁用') }}</option>
            </select>
          </label>
        </div>
        <label class="protocol-textarea">
          {{ tr('描述') }}
          <textarea :value="draft.desc" rows="3" :disabled="mode === 'view'" @input="updateDraft('desc', $event.target.value)"></textarea>
        </label>
        <div class="modal-section protocol-driver" v-if="editing && editing.driver">
          <div class="section-title">{{ tr('驱动') }}</div>
          <div class="form-grid protocol-grid">
            <label>
              {{ tr('驱动类') }}
              <input :value="editing.driver" type="text" disabled />
            </label>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" type="button" @click="emit('close')">{{ tr('取消') }}</button>
        <button v-if="mode !== 'view'" class="btn btn-primary" type="button" @click="emit('save')">{{ tr('保存') }}</button>
      </div>
    </div>
  </div>
</template>
