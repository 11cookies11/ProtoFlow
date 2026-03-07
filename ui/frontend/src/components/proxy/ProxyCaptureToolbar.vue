<script setup>
import { inject } from 'vue'

const tr = inject('tr', (text) => text)

const props = defineProps({
  captureProxy: {
    type: Object,
    default: null,
  },
  captureMeta: {
    type: Object,
    default: () => ({}),
  },
  searchKeyword: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:search-keyword', 'resume-capture', 'open-settings'])

function onSearchInput(event) {
  emit('update:search-keyword', event?.target?.value || '')
}

function onResumeCapture() {
  emit('resume-capture')
}

function onOpenSettings() {
  emit('open-settings')
}
</script>

<template>
  <div>
    <header class="px-4 py-3 flex items-center justify-between border-b border-slate-200 bg-white">
      <div class="flex items-center gap-4">
        <div class="p-1.5 bg-blue-100 rounded text-blue-600">
          <span class="material-symbols-outlined">analytics</span>
        </div>
        <div>
          <h1 class="text-sm font-bold text-slate-900 leading-none">{{ tr('多协议通用报文分析引擎') }}</h1>
          <div class="flex items-center gap-2 mt-1">
            <span class="flex h-2 w-2 rounded-full bg-emerald-500"></span>
            <p class="text-[10px] font-medium text-slate-500">
              {{ tr('活动通道') }}: {{ captureProxy ? captureProxy.hostPort : captureMeta.channel }} | {{ tr('引擎状态') }}:
              {{ tr(captureMeta.engine) }}
            </p>
          </div>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex items-center bg-slate-100 rounded-md px-2 border border-slate-200">
          <span class="material-symbols-outlined text-slate-400">search</span>
          <input
            class="bg-transparent border-none text-xs w-64 lg:w-96 focus:ring-0 text-slate-900 placeholder-slate-500"
            :placeholder="tr('搜索标识、十六进制、协议、原始数据...')"
            type="text"
            :value="props.searchKeyword"
            @input="onSearchInput"
          />
        </div>
        <div class="h-6 w-[1px] bg-slate-200 mx-1"></div>
        <button
          type="button"
          class="flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-bold transition-colors shadow-sm"
          @click="onResumeCapture"
        >
          <span class="material-symbols-outlined !text-sm">play_arrow</span>{{ tr('继续捕获') }}
        </button>
        <button type="button" class="p-1.5 hover:bg-slate-100 rounded text-slate-400" @click="onOpenSettings">
          <span class="material-symbols-outlined">settings</span>
        </button>
      </div>
    </header>
    <div class="h-1.5 w-full bg-slate-200 relative cursor-pointer group overflow-hidden">
      <div class="timeline-heatmap h-full w-full opacity-80 group-hover:opacity-100 transition-opacity"></div>
      <div class="absolute top-0 bottom-0 left-[20%] w-[5%] border-x border-white/50 bg-white/20 shadow-sm pointer-events-none"></div>
    </div>
  </div>
</template>
