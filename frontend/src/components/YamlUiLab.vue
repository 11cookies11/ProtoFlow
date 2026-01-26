<template>
  <div class="grid grid-cols-12 gap-6">
    <section class="col-span-12 lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-bold text-slate-800">{{ tr('YAML UI 编辑器') }}</h2>
        <span class="text-xs text-slate-400">{{ tr('实时渲染') }}</span>
      </div>
      <textarea
        class="w-full min-h-[520px] p-3 rounded-lg border border-slate-200 font-mono text-xs text-slate-700 focus:border-primary focus:ring-4 focus:ring-primary/10"
        :value="store.yamlText"
        @input="handleInput"
      ></textarea>
      <div v-if="store.parseError" class="text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-lg p-3">
        <div class="font-bold">{{ tr('解析错误') }}</div>
        <div>{{ store.parseError.message }}</div>
        <div v-if="store.parseError.path" class="mt-1">{{ tr('路径') }}: {{ store.parseError.path }}</div>
        <div v-if="store.parseError.line">{{ tr('行') }} {{ store.parseError.line }} {{ tr('列') }} {{ store.parseError.column }}</div>
      </div>
    </section>

    <section class="col-span-12 lg:col-span-7 space-y-6">
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <LayoutRenderer
          v-if="store.lastGoodConfig"
          :config="store.lastGoodConfig"
          :widgets-by-id="store.widgetsById"
        />
        <div v-else class="text-sm text-slate-400">{{ tr('等待 YAML 配置...') }}</div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <InspectorJSON
          title="Widget Inspector"
          :value="selectedWidget"
        />
        <EventLogPanel
          title="Event Log"
          :value="store.eventLog"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, inject } from 'vue'
import LayoutRenderer from '@/ui/LayoutRenderer.vue'
import InspectorJSON from '@/components/ui-kit/InspectorJSON.vue'
import EventLogPanel from '@/components/ui-kit/EventLogPanel.vue'
import { useUiRuntimeStore } from '@/stores/uiRuntime'

const store = useUiRuntimeStore()
const tr = inject('tr', (text) => text)

const selectedWidget = computed(() => {
  if (!store.selectedWidgetId) return null
  return store.widgetsById[store.selectedWidgetId] || null
})

function handleInput(event: Event) {
  const value = (event.target as HTMLTextAreaElement).value
  store.setYamlText(value)
  store.tryParseAndValidate()
}

onMounted(() => {
  const bridge = (window as unknown as { bridge?: any }).bridge
  if (bridge) {
    store.bindBridge(bridge)
  }
  store.tryParseAndValidate()
})
</script>
