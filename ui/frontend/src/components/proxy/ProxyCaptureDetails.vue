<script setup>
import { inject } from 'vue'

const tr = inject('tr', (text) => text)

defineProps({
  activeFrame: {
    type: Object,
    default: null,
  },
  isUnknownFrame: {
    type: Boolean,
    default: false,
  },
  activeProtocolLabel: {
    type: String,
    default: '',
  },
  activeHexSize: {
    type: Number,
    default: 0,
  },
  activeHexCells: {
    type: Array,
    default: () => [],
  },
  activeHexAscii: {
    type: Array,
    default: () => ['', ''],
  },
  activeTreeRows: {
    type: Array,
    default: () => [],
  },
  captureMetrics: {
    type: Object,
    default: () => ({ rtt: '', loss: '' }),
  },
  hexCellClass: {
    type: Function,
    default: () => '',
  },
})

const emit = defineEmits(['close', 'copy-hex', 'open-rule'])

function onClose() {
  emit('close')
}

function onCopyHex() {
  emit('copy-hex')
}

function onOpenRule(mode) {
  emit('open-rule', mode)
}
</script>

<template>
  <aside class="flex-1 w-[450px] flex flex-col border-l border-slate-200 bg-slate-50">
    <div class="px-4 py-3 border-b border-slate-200 flex justify-between items-center bg-white shadow-sm">
      <h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
        <span class="material-symbols-outlined !text-sm text-blue-500">info</span>{{ tr('报文解析详情') }}
      </h2>
      <div class="flex gap-2">
        <button
          type="button"
          class="p-1 hover:bg-slate-100 rounded"
          :title="!activeFrame ? tr('暂无可复制报文') : tr('复制原始十六进制')"
          :disabled="!activeFrame"
          @click="onCopyHex"
        >
          <span class="material-symbols-outlined !text-sm">content_copy</span>
        </button>
        <button type="button" class="p-1 hover:bg-slate-100 rounded" @click="onClose">
          <span class="material-symbols-outlined !text-sm">close</span>
        </button>
      </div>
    </div>
    <div class="flex-1 overflow-y-auto">
      <div v-if="!activeFrame" class="p-6 text-center text-slate-400 text-sm">{{ tr('暂无报文数据') }}</div>
      <template v-else>
        <div class="p-6 text-center space-y-4 border-b border-slate-200 bg-orange-50/20">
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-orange-100 text-orange-600 mb-1">
            <span class="material-symbols-outlined !text-3xl">question_mark</span>
          </div>
          <div>
            <h3 class="text-sm font-bold text-slate-800">
              {{ isUnknownFrame ? tr('未知协议报文 (Unknown Protocol)') : `${activeProtocolLabel} ${tr('报文')}` }}
            </h3>
            <p class="text-[11px] text-slate-500 mt-1 max-w-[280px] mx-auto leading-relaxed">
              {{
                isUnknownFrame
                  ? tr('系统未能自动匹配已知的解析插件。您可以尝试手动配置解析规则，或使用万能解析脚本。')
                  : tr('已匹配协议解析插件，当前展示该报文的解析详情。')
              }}
            </p>
          </div>
          <div class="flex justify-center gap-3">
            <button
              type="button"
              class="px-3 py-1.5 bg-white border border-slate-300 rounded text-[11px] font-bold hover:bg-slate-50 transition-colors shadow-sm"
              @click="onOpenRule('inspect')"
            >
              {{ isUnknownFrame ? tr('手动解析') : tr('查看详情') }}
            </button>
            <button
              type="button"
              class="px-3 py-1.5 bg-blue-600 text-white rounded text-[11px] font-bold hover:bg-blue-700 transition-colors flex items-center gap-1 shadow-md"
              @click="onOpenRule('configure')"
            >
              <span class="material-symbols-outlined !text-xs">schema</span>
              {{ isUnknownFrame ? tr('配置解析规则') : tr('调整解析规则') }}
            </button>
          </div>
        </div>
        <div class="p-4 border-b border-slate-200">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{{ tr('原始十六进制 (RAW HEX)') }}</h3>
            <span class="text-[10px] font-mono bg-slate-200 px-1.5 py-0.5 rounded text-slate-600">
              {{ activeHexSize }} {{ tr('字节') }}
            </span>
          </div>
          <div v-if="activeHexCells.length" class="bg-white border border-slate-200 rounded-lg overflow-hidden flex shadow-inner">
            <div class="bg-slate-50 border-r border-slate-200 p-2 text-[10px] font-mono text-slate-400 leading-6 text-right w-12 shrink-0">
              0000<br />0008
            </div>
            <div class="flex-1 p-2 hex-font text-xs leading-6 grid grid-cols-8 gap-x-1 text-center font-medium">
              <span
                v-for="(cell, cellIndex) in activeHexCells"
                :key="`hex-${cellIndex}`"
                :class="hexCellClass(cellIndex, cell)"
              >
                {{ cell }}
              </span>
            </div>
            <div class="border-l border-slate-200 p-2 text-[10px] font-mono text-slate-500 leading-6 tracking-tight w-24 shrink-0 bg-slate-50/50">
              {{ activeHexAscii[0] }}<br />{{ activeHexAscii[1] }}
            </div>
          </div>
          <div v-else class="text-xs text-slate-400">{{ tr('暂无十六进制数据') }}</div>
        </div>
        <div class="p-4 space-y-4">
          <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">{{ tr('协议层级解析 (PROTOCOL TREE)') }}</h3>
          <div class="relative pl-4 space-y-1">
            <div class="flex items-center gap-2 -ml-4 cursor-pointer hover:bg-slate-100 p-1 rounded transition-colors group">
              <span class="material-symbols-outlined text-slate-400 group-open:rotate-90">arrow_right</span>
              <span class="text-[11px] font-bold text-slate-500 uppercase">{{ tr('链路层 (Data Link Layer)') }}</span>
            </div>
            <div class="tree-line relative pl-2 space-y-1">
              <details class="group" open>
                <summary class="flex items-center gap-2 list-none cursor-pointer hover:bg-slate-100 p-1 rounded -ml-4 transition-colors">
                  <span class="material-symbols-outlined text-blue-500 group-open:rotate-90 transition-transform">arrow_drop_down</span>
                  <span class="text-[11px] font-bold text-slate-800 uppercase">{{ activeProtocolLabel }}</span>
                </summary>
                <div class="mt-2 space-y-0.5 pl-2">
                  <div class="grid grid-cols-12 text-[9px] font-bold text-slate-400 px-2 py-1 uppercase tracking-tighter">
                    <div class="col-span-3">{{ tr('原始值') }}</div>
                    <div class="col-span-4">{{ tr('字段') }}</div>
                    <div class="col-span-5 text-right">{{ tr('解析值') }}</div>
                  </div>
                  <div
                    v-for="(row, rowIndex) in activeTreeRows"
                    :key="`tree-${rowIndex}`"
                    class="grid grid-cols-12 items-center py-1.5 px-2 rounded hover:bg-blue-50 cursor-default transition-colors border-l-2 border-transparent hover:border-blue-500"
                  >
                    <div class="col-span-3 font-mono text-[11px] text-blue-600">{{ row.raw }}</div>
                    <div class="col-span-4 text-[11px] text-slate-500">{{ row.label }}</div>
                    <div class="col-span-5 text-[11px] text-right font-bold text-slate-700">{{ row.value }}</div>
                  </div>
                  <div v-if="!activeTreeRows.length" class="text-xs text-slate-400 px-2 py-2">{{ tr('暂无协议解析数据') }}</div>
                </div>
              </details>
            </div>
          </div>
        </div>
      </template>
    </div>
    <div class="p-4 bg-slate-100/50 border-t border-slate-200">
      <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">{{ tr('实时网络指标') }}</p>
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white p-2 rounded border border-slate-200 shadow-sm">
          <p class="text-[9px] text-slate-500">{{ tr('往返延时 (RTT)') }}</p>
          <p class="text-sm font-bold text-emerald-500">{{ captureMetrics.rtt }}</p>
        </div>
        <div class="bg-white p-2 rounded border border-slate-200 shadow-sm">
          <p class="text-[9px] text-slate-500">{{ tr('丢包率 (Packet Loss)') }}</p>
          <p class="text-sm font-bold text-slate-900">{{ captureMetrics.loss }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>
