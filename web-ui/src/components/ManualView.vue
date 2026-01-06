<script setup>
import { inject } from 'vue'
import DropdownSelect from './DropdownSelect.vue'
import LogStream from './LogStream.vue'

const bindings = inject('manualView')
if (!bindings) {
  throw new Error('manualView bindings not provided')
}

const {
  connectionInfo,
  isConnected,
  isConnecting,
  selectedPort,
  portOptionsList,
  portPlaceholder,
  noPorts,
  sendMode,
  sendText,
  sendHex,
  appendCR,
  appendLF,
  loopSend,
  displayMode,
  quickCommands,
  logTab,
  logKeyword,
  visibleCommLogs,
  renderedCommLogs,
  renderedVisibleCommLogs,
  formatTime,
  formatPayload,
  commPaused,
  clearCommLogs,
  toggleCommPaused,
  exportCommLogs,
  selectPort,
  refreshPorts,
  disconnect,
  connectSerial,
  sendPayload,
  sendQuickCommand,
} = bindings
</script>

<template>
  <section class="page">
          <header class="page-header">
            <div>
              <h2>手动脚本</h2>
              <p>单步调试指令发送与 I/O 数据流实时监控。</p>
            </div>
            <div class="header-actions">
              <div class="status-indicator" :class="connectionInfo.state">
                <span class="dot"></span>
                {{ isConnected ? '已连接' : connectionInfo.state === 'error' ? '错误' : '未连接' }}
              </div>
              <DropdownSelect
                v-model="selectedPort"
                :options="portOptionsList"
                :placeholder="portPlaceholder"
                :disabled="noPorts || isConnected || isConnecting"
                leading-icon="usb"
                @change="selectPort"
              />
              <button
                class="icon-btn"
                type="button"
                title="刷新串口"
                :disabled="isConnected || isConnecting"
                @click="refreshPorts"
              >
                <span class="material-symbols-outlined">refresh</span>
              </button>
              <button
                class="btn"
                :class="isConnected ? 'btn-danger' : 'btn-success'"
                :disabled="isConnecting && !isConnected"
                @click="isConnected ? disconnect() : connectSerial()"
              >
                <span class="material-symbols-outlined">link</span>
                {{ isConnected ? '断开' : isConnecting ? '连接中' : '连接' }}
              </button>
            </div>
          </header>

          <div class="manual-grid">
            <div class="manual-left">
              <div class="panel stack manual-send">
                <div class="panel-title">
                  <span class="material-symbols-outlined">send</span>
                  发送数据
                  <div class="segmented">
                    <button :class="{ active: sendMode === 'text' }" @click="sendMode = 'text'">文本</button>
                    <button :class="{ active: sendMode === 'hex' }" @click="sendMode = 'hex'">HEX</button>
                  </div>
                </div>
                <textarea
                  v-if="sendMode === 'text'"
                  v-model="sendText"
                  class="text-area"
                  placeholder="输入要发送的数据..."
                ></textarea>
                <textarea
                  v-else
                  v-model="sendHex"
                  class="text-area"
                  placeholder="55 AA 01"
                ></textarea>
                <div class="toggle-row">
                  <label class="check">
                    <input v-model="appendCR" type="checkbox" />
                    <span>+CR</span>
                  </label>
                  <label class="check">
                    <input v-model="appendLF" type="checkbox" />
                    <span>+LF</span>
                  </label>
                  <label class="check">
                    <input v-model="loopSend" type="checkbox" />
                    <span>循环发送</span>
                  </label>
                </div>
                <button class="btn btn-primary" @click="sendPayload">
                  <span class="material-symbols-outlined">send</span>
                  发送数据
                </button>
              </div>

              <div class="panel stack manual-quick">
                <div class="panel-title simple">
                  快捷指令
                  <button class="icon-btn">
                    <span class="material-symbols-outlined">add</span>
                  </button>
                </div>
                <div class="quick-list">
                  <button
                    :key="cmd"
                    class="quick-item"
                    @click="sendQuickCommand(cmd)"
                  >
                    <span>{{ cmd }}</span>
                    <span class="material-symbols-outlined">play_arrow</span>
                  </button>
                </div>
              </div>
            </div>

            <div class="manual-right">
              <div class="panel monitor manual-monitor">
                <div class="panel-title bar">
                  <div class="panel-title-left">
                    <span class="material-symbols-outlined">swap_horiz</span>
                    IO 监控
                    <span class="pill live">LIVE</span>
                  </div>
                  <div class="panel-actions">
                    <div class="segmented small">
                      <button :class="{ active: displayMode === 'ascii' }" @click="displayMode = 'ascii'">ASCII</button>
                      <button :class="{ active: displayMode === 'hex' }" @click="displayMode = 'hex'">HEX</button>
                    </div>
                    <span class="divider"></span>
                    <button class="icon-btn" type="button" title="??" @click="clearCommLogs">
                      <span class="material-symbols-outlined">delete</span>
                    </button>
                    <button
                      class="icon-btn"
                      type="button"
                      title="??"
                      :class="{ active: commPaused }"
                      @click="toggleCommPaused"
                    >
                      <span class="material-symbols-outlined">pause_circle</span>
                    </button>
                    <button class="icon-btn" type="button" title="??" @click="exportCommLogs">
                      <span class="material-symbols-outlined">download</span>
                    </button>
                  </div>
                </div>
                <LogStream
                  :items="renderedCommLogs"
                  :formatTime="formatTime"
                  :formatPayload="formatPayload"
                />
              </div>

              <div class="panel console manual-console">
                <div class="tab-strip">
                  <button :class="{ active: logTab === 'all' }" @click="logTab = 'all'">全部日志</button>
                  <button :class="{ active: logTab === 'uart' }" @click="logTab = 'uart'">串口 (UART)</button>
                  <button :class="{ active: logTab === 'tcp' }" @click="logTab = 'tcp'">网络 (TCP)</button>
                  <div class="search">
                    <span class="material-symbols-outlined">search</span>
                    <input v-model="logKeyword" type="text" placeholder="过滤日志..." />
                  </div>
                </div>
                <LogStream
                  compact
                  :items="renderedVisibleCommLogs"
                  :formatTime="formatTime"
                  :formatPayload="formatPayload"
                />
                <div class="panel-footer">
                  <span>{{ visibleCommLogs.length }} 条日志记录</span>
                  <button class="link-btn" type="button" @click="clearCommLogs">清除日志</button>
                </div>
              </div>
            </div>
          </div>
        </section>


</template>
