<script setup>
import { inject } from 'vue'

const tr = inject('tr', (text) => text)

defineProps({
  captureMeta: {
    type: Object,
    default: () => ({}),
  },
})
</script>

<template>
  <footer class="px-4 py-2 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
    <div class="flex items-center gap-6">
      <div class="flex items-center gap-2">
        <span class="text-[10px] font-bold text-slate-500 uppercase">{{ tr('接收缓冲区') }}</span>
        <div class="w-32 h-2 bg-slate-200 rounded-full overflow-hidden border border-slate-300">
          <div class="h-full bg-amber-500" :style="{ width: `${captureMeta.bufferUsed}%` }"></div>
        </div>
        <span class="text-[10px] font-mono font-bold text-slate-600">{{ captureMeta.bufferUsed }}%</span>
      </div>
      <div class="h-4 w-[1px] bg-slate-300"></div>
      <p class="text-[10px] font-medium text-slate-500 uppercase">
        {{ tr('显示') }} {{ captureMeta.rangeStart }}-{{ captureMeta.rangeEnd }} / {{ tr('共') }} {{ captureMeta.totalFrames }} {{ tr('报文') }}
      </p>
    </div>
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-1 bg-white p-0.5 rounded border border-slate-200">
        <button class="p-1 hover:bg-slate-100 rounded" disabled>
          <span class="material-symbols-outlined !text-sm">first_page</span>
        </button>
        <button class="p-1 hover:bg-slate-100 rounded">
          <span class="material-symbols-outlined !text-sm">chevron_left</span>
        </button>
        <div class="px-3 text-[10px] font-bold text-slate-700">{{ tr('第') }} {{ captureMeta.page }} / {{ captureMeta.pageCount }} {{ tr('页') }}</div>
        <button class="p-1 hover:bg-slate-100 rounded">
          <span class="material-symbols-outlined !text-sm">chevron_right</span>
        </button>
        <button class="p-1 hover:bg-slate-100 rounded">
          <span class="material-symbols-outlined !text-sm">last_page</span>
        </button>
      </div>
      <button class="flex items-center gap-1 px-3 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded text-[10px] font-bold transition-colors">
        <span class="material-symbols-outlined !text-sm">download</span>{{ tr('导出分析结果') }}
      </button>
    </div>
  </footer>
</template>
