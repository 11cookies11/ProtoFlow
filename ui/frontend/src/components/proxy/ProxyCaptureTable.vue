<script setup>
import { inject } from 'vue'

const tr = inject('tr', (text) => text)

const props = defineProps({
  visibleFrames: {
    type: Array,
    default: () => [],
  },
  captureMeta: {
    type: Object,
    default: () => ({}),
  },
  frameWindow: {
    type: Object,
    default: () => ({ range: { start: 0, topOffset: 0, bottomOffset: 0 } }),
  },
})

const emit = defineEmits(['select-frame'])

function onSelectFrame(frame) {
  emit('select-frame', frame)
}
</script>

<template>
  <section class="flex-[2] flex flex-col min-w-0 bg-white">
    <div class="overflow-auto flex-1">
      <table class="w-full text-left border-separate border-spacing-0">
        <thead class="sticky top-0 z-10 bg-slate-50 shadow-sm">
          <tr class="text-[10px] uppercase tracking-wider font-bold text-slate-500">
            <th class="px-3 py-2 border-b border-slate-200 w-16">{{ tr('序号') }}</th>
            <th class="px-3 py-2 border-b border-slate-200 w-28">{{ tr('时间戳') }}</th>
            <th class="px-3 py-2 border-b border-slate-200 w-12 text-center">{{ tr('方向') }}</th>
            <th class="px-3 py-2 border-b border-slate-200 w-32">{{ tr('协议') }}</th>
            <th class="px-3 py-2 border-b border-slate-200 w-16">{{ tr('长度') }}</th>
            <th class="px-3 py-2 border-b border-slate-200 w-72">{{ tr('原始数据') }}</th>
            <th class="px-3 py-2 border-b border-slate-200">{{ tr('摘要 (解析结果/HEX/ASCII)') }}</th>
          </tr>
        </thead>
        <tbody class="text-xs">
          <tr v-if="frameWindow.range.topOffset > 0">
            <td :colspan="7" :style="{ height: `${frameWindow.range.topOffset}px` }"></td>
          </tr>
          <tr
            v-for="(frame, index) in visibleFrames"
            :key="frame?.id ?? `${frameWindow.range.start + index}`"
            class="hover:bg-slate-50 cursor-pointer border-b border-slate-100"
            :class="{ 'bg-orange-50/40 border-l-4 border-l-orange-400': frame.tone === 'red' }"
            @click="onSelectFrame(frame)"
          >
            <td class="px-3 py-2 text-slate-400 font-mono">
              {{
                frame.seq ??
                (captureMeta.rangeStart
                  ? captureMeta.rangeStart + frameWindow.range.start + index
                  : frameWindow.range.start + index + 1)
              }}
            </td>
            <td class="px-3 py-2 text-slate-500 font-mono">{{ frame.time }}</td>
            <td class="px-3 py-2 text-center">
              <span
                class="material-symbols-outlined !text-sm"
                :class="frame.direction === 'RX' ? 'text-emerald-500' : 'text-blue-500'"
              >
                {{ frame.direction === 'RX' ? 'arrow_downward' : 'arrow_upward' }}
              </span>
            </td>
            <td class="px-3 py-2">
              <div class="relative inline-block protocol-badge">
                <div
                  class="flex items-center gap-1.5 px-2 py-0.5 rounded-full font-bold text-[9px] border"
                  :class="
                    frame.tone === 'red'
                      ? 'bg-slate-100 text-slate-600 border-dashed border-slate-300'
                      : 'bg-blue-100 text-blue-800 border-blue-200'
                  "
                >
                  <span
                    class="w-3.5 h-3.5 flex items-center justify-center text-white rounded-full text-[8px] font-black"
                    :class="frame.tone === 'red' ? 'bg-slate-400' : 'bg-blue-600'"
                  >
                    {{ frame.tone === 'red' ? '?' : 'M' }}
                  </span>
                  <span>{{ frame.protocolLabel || '' }}</span>
                </div>
                <div class="protocol-tooltip bg-slate-800 text-white text-[10px] px-2 py-1 rounded shadow-lg pointer-events-none whitespace-nowrap border border-slate-700">
                  {{ frame.protocolTooltip || '' }}
                </div>
              </div>
            </td>
            <td class="px-3 py-2 text-slate-500">{{ frame.size }}B</td>
            <td class="px-3 py-2 hex-font text-slate-400 truncate max-w-[240px]">{{ frame.note }}</td>
            <td class="px-3 py-2 text-slate-600 italic">
              {{ frame.summaryText || frame.summary || '' }}
            </td>
          </tr>
          <tr v-if="frameWindow.range.bottomOffset > 0">
            <td :colspan="7" :style="{ height: `${frameWindow.range.bottomOffset}px` }"></td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
