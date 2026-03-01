<script setup>
import { inject } from 'vue'
import DropdownSelect from '@/components/DropdownSelect.vue'

const tr = inject('tr', (text) => text)

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  mode: {
    type: String,
    default: 'edit',
  },
  formError: {
    type: String,
    default: '',
  },
  proxyName: {
    type: String,
    default: '',
  },
  connectionMode: {
    type: String,
    default: '',
  },
  hostPort: {
    type: String,
    default: '',
  },
  devicePort: {
    type: String,
    default: '',
  },
  baudRate: {
    type: String,
    default: '',
  },
  dataBits: {
    type: String,
    default: '8',
  },
  stopBits: {
    type: String,
    default: '1',
  },
  parity: {
    type: String,
    default: 'none',
  },
  flowControl: {
    type: String,
    default: 'none',
  },
  connectionOptions: {
    type: Array,
    default: () => [],
  },
  portOptions: {
    type: Array,
    default: () => [],
  },
  baudOptions: {
    type: Array,
    default: () => [],
  },
  parityOptions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits([
  'close',
  'save',
  'update:proxyName',
  'update:connectionMode',
  'update:hostPort',
  'update:devicePort',
  'update:baudRate',
  'update:dataBits',
  'update:stopBits',
  'update:parity',
  'update:flowControl',
])
</script>

<template>
  <div v-if="open" class="proxy-modal-overlay">
    <div class="proxy-modal" @mousedown.stop @click.stop>
      <div class="proxy-modal-header">
        <div class="proxy-modal-title">
          <div class="proxy-modal-icon">
            <span class="material-symbols-outlined">edit_square</span>
          </div>
          <h2>{{ mode === 'create' ? tr('新建转发对') : tr('编辑转发代理') }}</h2>
        </div>
        <button class="proxy-modal-close" type="button" @click="emit('close')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="proxy-modal-body">
        <div class="proxy-modal-stack">
          <div class="proxy-modal-grid">
            <div class="proxy-field">
              <label>{{ tr('代理名称') }}</label>
              <input type="text" :value="proxyName" @input="emit('update:proxyName', $event.target.value)" />
            </div>
            <div class="proxy-field">
              <label>{{ tr('连接模式') }}</label>
              <DropdownSelect
                class="proxy-select"
                :model-value="connectionMode"
                :options="connectionOptions"
                @update:model-value="emit('update:connectionMode', $event)"
              />
            </div>
          </div>
          <div class="proxy-port-map">
            <div class="proxy-field">
              <label>
                <span class="material-symbols-outlined">computer</span>{{ tr('主机端口') }}
              </label>
              <DropdownSelect
                class="proxy-select"
                :model-value="hostPort"
                :options="portOptions"
                @update:model-value="emit('update:hostPort', $event)"
              />
            </div>
            <div class="proxy-field">
              <label>
                <span class="material-symbols-outlined">settings_input_component</span>{{ tr('设备端口') }}
              </label>
              <DropdownSelect
                class="proxy-select"
                :model-value="devicePort"
                :options="portOptions"
                @update:model-value="emit('update:devicePort', $event)"
              />
            </div>
          </div>
          <div v-if="formError" class="text-xs text-rose-500 -mt-1">{{ formError }}</div>
          <div class="proxy-section">
            <div class="proxy-section-title">
              <span class="material-symbols-outlined">settings_ethernet</span>{{ tr('串口参数配置') }}<span>{{ tr('（两端需一致）') }}</span>
            </div>
            <div class="proxy-section-grid">
              <div class="proxy-field">
                <label>{{ tr('波特率') }}</label>
                <DropdownSelect
                  class="proxy-select"
                  :model-value="baudRate"
                  :options="baudOptions"
                  @update:model-value="emit('update:baudRate', $event)"
                />
              </div>
              <div class="proxy-field">
                <label>{{ tr('数据位') }}</label>
                <div class="proxy-segmented">
                  <button type="button" :class="{ active: dataBits === '5' }" @click="emit('update:dataBits', '5')">5</button>
                  <button type="button" :class="{ active: dataBits === '6' }" @click="emit('update:dataBits', '6')">6</button>
                  <button type="button" :class="{ active: dataBits === '7' }" @click="emit('update:dataBits', '7')">7</button>
                  <button type="button" :class="{ active: dataBits === '8' }" @click="emit('update:dataBits', '8')">8</button>
                </div>
              </div>
              <div class="proxy-field">
                <label>{{ tr('校验位') }}</label>
                <DropdownSelect
                  class="proxy-select"
                  :model-value="parity"
                  :options="parityOptions"
                  @update:model-value="emit('update:parity', $event)"
                />
              </div>
              <div class="proxy-field">
                <label>{{ tr('停止位') }}</label>
                <div class="proxy-segmented">
                  <button type="button" :class="{ active: stopBits === '1' }" @click="emit('update:stopBits', '1')">1</button>
                  <button type="button" :class="{ active: stopBits === '1.5' }" @click="emit('update:stopBits', '1.5')">1.5</button>
                  <button type="button" :class="{ active: stopBits === '2' }" @click="emit('update:stopBits', '2')">2</button>
                </div>
              </div>
              <div class="proxy-field proxy-span-2">
                <label>{{ tr('流控') }}</label>
                <div class="proxy-segmented">
                  <button type="button" :class="{ active: flowControl === 'none' }" @click="emit('update:flowControl', 'none')">None</button>
                  <button type="button" :class="{ active: flowControl === 'rtscts' }" @click="emit('update:flowControl', 'rtscts')">RTS/CTS</button>
                  <button type="button" :class="{ active: flowControl === 'xonxoff' }" @click="emit('update:flowControl', 'xonxoff')">XON/XOFF</button>
                </div>
              </div>
            </div>
          </div>
          <div class="proxy-section proxy-modal-advanced">
            <div class="proxy-section-title muted">
              <span class="material-symbols-outlined">settings_suggest</span>{{ tr('高级选项') }}
            </div>
            <div class="proxy-toggle-row">
              <label>
                <span class="proxy-toggle">
                  <input type="checkbox" checked />
                  <span></span>
                </span>{{ tr('自动重连') }}
              </label>
              <label>
                <span class="proxy-toggle">
                  <input type="checkbox" />
                  <span></span>
                </span>{{ tr('详细日志') }}
              </label>
            </div>
          </div>
        </div>
      </div>
      <div class="proxy-modal-footer">
        <div></div>
        <div class="proxy-footer-actions">
          <button class="proxy-btn ghost" type="button" @click="emit('close')">{{ tr('取消') }}</button>
          <button class="proxy-btn primary" type="button" @click="emit('save')">{{ tr('保存') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
