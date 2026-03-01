<script setup>
import { inject } from 'vue'
import DropdownSelect from './DropdownSelect.vue'

const tr = inject('tr', (text) => text)

defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'create' },
  channelType: { type: String, default: 'serial' },
  channelName: { type: String, default: '' },
  channelPort: { type: String, default: '' },
  channelBaud: { type: [String, Number], default: 115200 },
  channelDataBits: { type: [String, Number], default: '8' },
  channelParity: { type: String, default: 'none' },
  channelStopBits: { type: [String, Number], default: '1' },
  channelFlowControl: { type: String, default: 'none' },
  channelReadTimeout: { type: [String, Number], default: 1000 },
  channelWriteTimeout: { type: [String, Number], default: 1000 },
  channelHost: { type: String, default: '' },
  channelTcpPort: { type: [String, Number], default: 0 },
  channelAutoConnect: { type: Boolean, default: true },
  hasPorts: { type: Boolean, default: false },
  portOptionsList: { type: Array, default: () => [] },
  supportedBaudRates: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'close',
  'submit',
  'update:channelType',
  'update:channelName',
  'update:channelPort',
  'update:channelBaud',
  'update:channelDataBits',
  'update:channelParity',
  'update:channelStopBits',
  'update:channelFlowControl',
  'update:channelReadTimeout',
  'update:channelWriteTimeout',
  'update:channelHost',
  'update:channelTcpPort',
  'update:channelAutoConnect',
])
</script>

<template>
  <div v-if="open" class="modal-backdrop">
    <div class="channel-modal">
      <div class="modal-header">
        <div>
          <h3>{{ mode === 'serial' ? tr('串口配置') : tr('新建通道') }}</h3>
          <p>{{ mode === 'serial' ? tr('配置串口连接参数') : tr('配置新的通信连接参数') }}</p>
        </div>
        <button class="icon-btn" type="button" @click="emit('close')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="modal-body">
        <div v-if="mode !== 'serial'" class="channel-type-grid">
          <button
            class="channel-type-card"
            :class="{ active: channelType === 'serial' }"
            type="button"
            @click="emit('update:channelType', 'serial')"
          >
            <span class="material-symbols-outlined">settings_input_hdmi</span>
            <span>{{ tr('串口 (Serial)') }}</span>
          </button>
          <button
            class="channel-type-card"
            :class="{ active: channelType === 'tcp' }"
            type="button"
            @click="emit('update:channelType', 'tcp')"
          >
            <span class="material-symbols-outlined">lan</span>
            <span>{{ tr('TCP / 网络') }}</span>
          </button>
        </div>

        <div class="modal-section" v-if="mode !== 'serial'">
          <div class="section-title">{{ tr('基本信息') }}</div>
          <div class="form-grid">
            <label>
              {{ tr('通道名称') }}
              <input :value="channelName" type="text" :placeholder="tr('例如：传感器A接口')" @input="emit('update:channelName', $event.target.value)" />
            </label>
            <label v-if="channelType === 'serial'">
              {{ tr('串口端口') }}
              <DropdownSelect
                :model-value="channelPort"
                :options="portOptionsList"
                :placeholder="hasPorts ? tr('选择串口') : tr('无可用串口')"
                leading-icon="usb"
                @update:model-value="emit('update:channelPort', $event)"
              />
            </label>
            <label v-else>
              {{ tr('目标地址') }}
              <input :value="channelHost" type="text" :placeholder="tr('例如：192.168.1.10')" @input="emit('update:channelHost', $event.target.value)" />
            </label>
          </div>
        </div>

        <div class="modal-section first" v-if="channelType === 'serial'">
          <div class="section-title">{{ tr('串口参数') }}</div>
          <div class="form-grid triple">
            <label>
              {{ tr('波特率') }}
              <DropdownSelect :model-value="channelBaud" :options="supportedBaudRates" @update:model-value="emit('update:channelBaud', $event)" />
            </label>
            <label>
              {{ tr('数据位') }}
              <DropdownSelect :model-value="channelDataBits" :options="['7', '8']" @update:model-value="emit('update:channelDataBits', $event)" />
            </label>
            <label>
              {{ tr('停止位') }}
              <DropdownSelect :model-value="channelStopBits" :options="['1', '1.5', '2']" @update:model-value="emit('update:channelStopBits', $event)" />
            </label>
          </div>
          <div class="form-grid quad">
            <label>
              {{ tr('校验位') }}
              <DropdownSelect
                :model-value="channelParity"
                :options="[
                  { label: tr('无校验'), value: 'none' },
                  { label: tr('奇校验'), value: 'odd' },
                  { label: tr('偶校验'), value: 'even' },
                ]"
                @update:model-value="emit('update:channelParity', $event)"
              />
            </label>
            <label>
              {{ tr('流控') }}
              <DropdownSelect
                :model-value="channelFlowControl"
                :options="[
                  { label: tr('无'), value: 'none' },
                  { label: 'RTS/CTS', value: 'rtscts' },
                  { label: 'XON/XOFF', value: 'xonxoff' },
                ]"
                @update:model-value="emit('update:channelFlowControl', $event)"
              />
            </label>
            <label>
              {{ tr('读超时 (ms)') }}
              <input :value="channelReadTimeout" type="number" min="0" placeholder="1000" @input="emit('update:channelReadTimeout', Number($event.target.value || 0))" />
            </label>
            <label>
              {{ tr('写超时 (ms)') }}
              <input :value="channelWriteTimeout" type="number" min="0" placeholder="1000" @input="emit('update:channelWriteTimeout', Number($event.target.value || 0))" />
            </label>
          </div>
        </div>

        <div class="modal-section" v-else>
          <div class="form-grid">
            <label>
              {{ tr('TCP 端口') }}
              <input :value="channelTcpPort" type="number" @input="emit('update:channelTcpPort', Number($event.target.value || 0))" />
            </label>
          </div>
        </div>

        <label class="channel-toggle">
          <input :checked="channelAutoConnect" type="checkbox" @change="emit('update:channelAutoConnect', $event.target.checked)" />
          <span>{{ mode === 'serial' ? tr('保存后立即连接') : tr('创建后立即启动连接') }}</span>
        </label>
      </div>
      <div class="modal-footer">
        <button class="btn btn-outline" type="button" @click="emit('close')">{{ tr('取消') }}</button>
        <button class="btn btn-primary" type="button" @click="emit('submit')">
          {{ mode === 'serial' ? tr('保存配置') : tr('创建通道') }}
        </button>
      </div>
    </div>
  </div>
</template>
