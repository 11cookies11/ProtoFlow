<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const seqKey = '__protoflowDropdownSeq__'
const registryKey = '__protoflowDropdownRegistry__'
const openKey = '__protoflowDropdownOpenId__'
const dropdownRegistry =
  globalThis[registryKey] instanceof Map ? globalThis[registryKey] : (globalThis[registryKey] = new Map())
const nextDropdownId = () => {
  const next = (Number(globalThis[seqKey]) || 0) + 1
  globalThis[seqKey] = next
  return next
}

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  options: {
    type: Array,
    default: () => [],
  },
  placeholder: {
    type: String,
    default: '--',
  },
  leadingIcon: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])
const rootRef = ref(null)
const open = ref(false)
const dropdownId = nextDropdownId()
const menuRef = ref(null)
const menuStyle = ref({})
const getOpenId = () => globalThis[openKey]
const setOpenId = (value) => {
  globalThis[openKey] = value
}

const normalizedOptions = computed(() => {
  return (props.options || []).map((item) => {
    if (typeof item === 'string' || typeof item === 'number') {
      return { label: String(item), value: item }
    }
    return {
      label: String(item.label ?? item.value ?? ''),
      value: item.value ?? item.label ?? '',
      icon: item.icon || '',
      disabled: Boolean(item.disabled),
    }
  })
})

const selectedLabel = computed(() => {
  const found = normalizedOptions.value.find((item) => item.value === props.modelValue)
  return found ? found.label : props.placeholder
})

function toggle() {
  if (props.disabled) return
  if (open.value) {
    close()
    return
  }
  dropdownRegistry.forEach((closeFn, key) => {
    if (key !== dropdownId) closeFn()
  })
  open.value = true
  setOpenId(dropdownId)
  document.body.classList.add('dropdown-open')
  window.dispatchEvent(new CustomEvent('dropdown:open', { detail: dropdownId }))
  nextTick(() => scheduleMenuPosition())
}

function close() {
  open.value = false
  if (getOpenId() === dropdownId) {
    setOpenId(null)
  }
  if (getOpenId() == null) {
    document.body.classList.remove('dropdown-open')
  }
}

function select(value) {
  if (props.disabled) return
  emit('update:modelValue', value)
  emit('change', value)
  close()
}

function updateMenuPosition() {
  if (!rootRef.value || !menuRef.value) return
  const rect = rootRef.value.getBoundingClientRect()
  const menuHeight = menuRef.value.offsetHeight || 0
  let top = rect.bottom + 6
  if (top + menuHeight > window.innerHeight - 8) {
    top = rect.top - menuHeight - 6
  }
  if (top < 8) top = 8
  menuStyle.value = {
    top: `${top}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
  }
}

function scheduleMenuPosition() {
  if (!open.value) return
  requestAnimationFrame(() => updateMenuPosition())
  requestAnimationFrame(() => updateMenuPosition())
}

function handlePointerDown(event) {
  if (!rootRef.value || !event) return
  if (
    !rootRef.value.contains(event.target) &&
    (!menuRef.value || !menuRef.value.contains(event.target))
  ) {
    close()
  }
}

function handleKeydown(event) {
  if (!event) return
  if (event.key === 'Escape') {
    close()
  }
}

function handleViewportChange() {
  if (!open.value) return
  scheduleMenuPosition()
}

function handleExternalOpen(event) {
  if (!event || event.detail === dropdownId) return
  close()
}

onMounted(() => {
  dropdownRegistry.set(dropdownId, close)
  window.addEventListener('pointerdown', handlePointerDown, true)
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('dropdown:open', handleExternalOpen)
  window.addEventListener('scroll', handleViewportChange, true)
  window.addEventListener('resize', handleViewportChange)
})

onBeforeUnmount(() => {
  dropdownRegistry.delete(dropdownId)
  window.removeEventListener('pointerdown', handlePointerDown, true)
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('dropdown:open', handleExternalOpen)
  window.removeEventListener('scroll', handleViewportChange, true)
  window.removeEventListener('resize', handleViewportChange)
  close()
  if (getOpenId() === dropdownId) {
    setOpenId(null)
  }
})
</script>

<template>
  <div class="select-wrap" ref="rootRef">
    <button class="select-trigger" type="button" @click.stop="toggle" :disabled="disabled">
      <span v-if="leadingIcon" class="material-symbols-outlined">{{ leadingIcon }}</span>
      <span class="select-value">{{ selectedLabel }}</span>
      <span class="material-symbols-outlined expand">expand_more</span>
    </button>
    <teleport to="body">
      <div v-if="open" ref="menuRef" class="select-menu" :style="menuStyle" @click.stop>
        <button
          v-for="item in normalizedOptions"
          :key="String(item.value)"
          class="select-option"
          :class="{ selected: item.value === modelValue }"
          type="button"
          :disabled="disabled || item.disabled"
          @click="select(item.value)"
        >
          <span v-if="item.icon" class="material-symbols-outlined">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </button>
      </div>
    </teleport>
  </div>
</template>
