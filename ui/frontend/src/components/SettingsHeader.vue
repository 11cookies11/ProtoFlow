<script setup>
import { inject } from 'vue'

const t = inject('t', (key) => key)

defineProps({
  settingsDirty: {
    type: Boolean,
    default: false,
  },
  settingsSaving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['discard', 'save'])
</script>

<template>
  <header class="page-header spaced">
    <div>
      <h2>{{ t('header.settings.title') }}</h2>
      <p>{{ t('header.settings.desc') }}</p>
    </div>
    <div class="header-actions">
      <button class="btn btn-outline" :disabled="!settingsDirty" @click="emit('discard')">{{ t('action.discardChanges') }}</button>
      <button class="btn btn-primary" :disabled="!settingsDirty || settingsSaving" @click="emit('save')">
        <span class="material-symbols-outlined">save</span>{{ t('action.saveChanges') }}
      </button>
    </div>
  </header>
</template>
