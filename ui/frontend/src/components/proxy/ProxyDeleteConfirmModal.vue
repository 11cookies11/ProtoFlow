<script setup>
import { inject } from 'vue'

const tr = inject('tr', (text) => text)

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  confirmProxy: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'confirm'])

function onClose() {
  emit('close')
}

function onConfirm() {
  emit('confirm')
}
</script>

<template>
  <div v-if="open" class="proxy-modal-overlay" @mousedown.self="onClose">
    <div class="proxy-modal proxy-confirm-modal" @mousedown.stop @click.stop>
      <div class="proxy-modal-header">
        <div class="proxy-modal-title">
          <div class="proxy-modal-icon">
            <span class="material-symbols-outlined">warning</span>
          </div>
          <h2>{{ tr('确认删除') }}</h2>
        </div>
        <button class="proxy-modal-close" type="button" @click="onClose">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="proxy-modal-body">
        <p class="proxy-confirm-text">
          {{ tr('确认删除转发对') }}「{{ confirmProxy?.name || tr('未命名转发对') }}」{{ tr('吗？') }}{{ tr('删除前将停止转发。') }}
        </p>
      </div>
      <div class="proxy-modal-footer">
        <div></div>
        <div class="proxy-footer-actions">
          <button class="proxy-btn ghost" type="button" @click="onClose">{{ tr('取消') }}</button>
          <button class="proxy-btn warning" type="button" @click="onConfirm">{{ tr('确认删除') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
