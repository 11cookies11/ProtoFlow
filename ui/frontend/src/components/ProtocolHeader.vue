<script setup>
import { inject } from 'vue'

const t = inject('t', (key) => key)

const emit = defineEmits(['refresh', 'create'])
</script>

<template>
  <header class="page-header spaced">
    <div>
      <h2>{{ t('header.protocols.title') }}</h2>
      <p>{{ t('header.protocols.desc') }}</p>
    </div>
    <div class="header-actions">
      <button class="btn btn-outline" @click="emit('refresh')">
        <span class="material-symbols-outlined">refresh</span>
        {{ t('action.refresh') }}
      </button>
      <button class="btn btn-primary" @click="emit('create')">
        <span class="material-symbols-outlined">add</span>
        {{ t('action.createProtocol') }}
      </button>
    </div>
  </header>
</template>
