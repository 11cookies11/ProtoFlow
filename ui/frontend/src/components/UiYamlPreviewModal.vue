<script setup>
import { inject } from 'vue'
import LayoutRenderer from '../ui/LayoutRenderer.vue'

const tr = inject('tr', (text) => text)

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  runtime: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['close'])
</script>

<template>
  <div v-if="open" class="modal-backdrop" @mousedown.self="emit('close')">
    <div class="channel-modal ui-yaml-modal" @mousedown.stop @click.stop>
      <div class="modal-header">
        <div>
          <h3>{{ tr('UI YAML 预览') }}</h3>
          <p>{{ tr('脚本运行中展示 UI 渲染结果') }}</p>
        </div>
        <button class="icon-btn" type="button" @click="emit('close')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="modal-body ui-yaml-body">
        <div v-if="runtime.parseError" class="ui-yaml-error">
          <strong>{{ tr('解析失败') }}</strong>
          <div>{{ runtime.parseError.message }}</div>
          <div v-if="runtime.parseError.path" class="muted">Path: {{ runtime.parseError.path }}</div>
          <div v-if="runtime.parseError.line" class="muted">
            Line {{ runtime.parseError.line }}, Column {{ runtime.parseError.column || 0 }}
          </div>
        </div>
        <div v-else-if="runtime.lastGoodConfig">
          <LayoutRenderer :config="runtime.lastGoodConfig" :widgetsById="runtime.widgetsById" />
        </div>
        <div v-else class="empty-state muted">{{ tr('暂无可渲染的 UI 配置') }}</div>
      </div>
    </div>
  </div>
</template>
