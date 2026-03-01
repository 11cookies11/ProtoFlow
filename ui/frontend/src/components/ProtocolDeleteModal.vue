<script setup>
import { inject } from 'vue'

const tr = inject('tr', (text) => text)

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  deleting: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'confirm'])
</script>

<template>
  <div v-if="open" class="modal-backdrop" @mousedown.self="emit('close')">
    <div class="quick-modal quick-modal-sm" @mousedown.stop @click.stop>
      <div class="modal-header">
        <div>
          <h3>{{ tr('删除协议') }}</h3>
          <p>{{ tr('确认删除自定义协议') }}“{{ deleting?.name }}”{{ tr('吗？') }}</p>
        </div>
        <button class="icon-btn" type="button" @click="emit('close')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" type="button" @click="emit('close')">{{ tr('取消') }}</button>
        <button class="btn btn-danger" type="button" @click="emit('confirm')">{{ tr('确认删除') }}</button>
      </div>
    </div>
  </div>
</template>
