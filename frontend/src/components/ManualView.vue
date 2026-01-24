<script setup>
import { inject } from 'vue'
import DropdownSelect from './DropdownSelect.vue'
import LogStream from './LogStream.vue'

const t = inject('t', (key) => key)
const tr = inject('tr', (text) => text)
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
  quickDialogOpen,
  quickDialogMode,
  quickDraft,
  quickPayloadCount,
  quickPayloadLimit,
  openQuickCommandDialog,
  closeQuickCommandDialog,
  saveQuickCommand,
  quickDeleteOpen,
  quickDeleting,
  openQuickDeleteDialog,
  closeQuickDeleteDialog,
  confirmQuickDelete,
  addQuickCommand,
  editQuickCommand,
  removeQuickCommand,
  selectPort,
  refreshPorts,
  disconnect,
  connectSerial,
  openChannelSettings,
  sendPayload,
  sendQuickCommand,
} = bindings
</script>

<template>
  <section class="page">
          <header class="page-header spaced">
            <div>
              <h2>{{ t('header.manual.title') }}</h2>
              <p>{{ t('header.manual.desc') }}</p>
            </div>
            <div class="header-actions terminal-config-actions">
              <div class="config-status">
                <div class="status-pill" :class="connectionInfo.state">
                  <span class="dot"></span>
                  {{ isConnected ? t('status.connected') : connectionInfo.state === 'error' ? t('status.error') : t('status.disconnected') }}
                </div>
              </div>
              <div class="port-picker terminal-port-picker">
                <DropdownSelect
                  v-model="selectedPort"
                  :options="portOptionsList"
                  :placeholder="portPlaceholder"
                  :disabled="noPorts || isConnected || isConnecting"
                  leading-icon="usb"
                  @change="selectPort"
                />
                <button class="icon-btn" type="button" :title="tr('串口设置')" @click="openChannelSettings">
                  <span class="material-symbols-outlined">settings</span>
                </button>
                <button
                  class="icon-btn refresh-icon"
                  type="button"
                  :title="tr('刷新串口')"
                  :disabled="isConnected || isConnecting"
                  @click="refreshPorts"
                >
                  <span class="material-symbols-outlined">refresh</span>
                </button>
              </div>
              <div class="config-controls terminal-config-controls">
                <button
                  class="btn"
                  :class="isConnected ? 'btn-danger' : 'btn-success'"
                  :disabled="isConnecting && !isConnected"
                  @click="isConnected ? disconnect() : connectSerial()"
                >
                  <span class="material-symbols-outlined">link</span>
                  {{ isConnected ? t('action.disconnect') : isConnecting ? t('status.connecting') : t('action.connect') }}
                </button>
              </div>
            </div>
          </header>

          <div class="manual-grid">
            <div class="manual-left">
              <div class="panel stack manual-send">
                <div class="panel-title">
                  <span class="material-symbols-outlined">send</span>{{ tr('发送数据') }}<div class="segmented">
                    <button :class="{ active: sendMode === 'text' }" @click="sendMode = 'text'">{{ tr('文本') }}</button>
                    <button :class="{ active: sendMode === 'hex' }" @click="sendMode = 'hex'">HEX</button>
                  </div>
                </div>
                <textarea
                  v-if="sendMode === 'text'"
                  v-model="sendText"
                  class="text-area"
                  :placeholder="tr('输入要发送的数据...')"
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
                    <span>{{ tr('循环发送') }}</span>
                  </label>
                </div>
                <button class="btn btn-primary" @click="sendPayload">
                  <span class="material-symbols-outlined">send</span>{{ tr('发送数据') }}</button>
              </div>

              <div class="panel stack manual-quick">
                <div class="panel-title simple">{{ tr('快捷指令') }}<button class="icon-btn" type="button" :title="tr('新增快捷指令')" @click="addQuickCommand">
                    <span class="material-symbols-outlined">add</span>
                  </button>
                </div>
                <div class="quick-list">
                  <button
                    v-for="cmd in quickCommands"
                    :key="cmd.id"
                    class="quick-item"
                    @click="sendQuickCommand(cmd)"
                  >
                    <div class="quick-info">
                      <span class="quick-title">{{ cmd.name }}</span>
                      <span class="quick-meta">{{ cmd.mode === 'hex' ? 'HEX' : tr('文本') }}</span>
                    </div>
                    <div class="quick-item-actions">
                      <button class="icon-btn small" type="button" :title="tr('编辑')" @click.stop="editQuickCommand(cmd)">
                        <span class="material-symbols-outlined">edit</span>
                      </button>
                      <button class="icon-btn small" type="button" :title="tr('删除')" @click.stop="openQuickDeleteDialog(cmd)">
                        <span class="material-symbols-outlined">delete</span>
                      </button>
                      <span class="material-symbols-outlined">play_arrow</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>

            <div class="manual-right">
              <div class="panel monitor manual-monitor">
                <div class="panel-title bar">
                  <div class="panel-title-left">
                    <span class="material-symbols-outlined">swap_horiz</span>{{ tr('IO 监控') }}<span class="pill live">LIVE</span>
                  </div>
                  <div class="panel-actions">
                    <div class="segmented small">
                      <button :class="{ active: displayMode === 'ascii' }" @click="displayMode = 'ascii'">ASCII</button>
                      <button :class="{ active: displayMode === 'hex' }" @click="displayMode = 'hex'">HEX</button>
                    </div>
                    <span class="divider"></span>
                    <button class="icon-btn" type="button" :title="tr('清除')" @click="clearCommLogs">
                      <span class="material-symbols-outlined">delete</span>
                    </button>
                    <button
                      class="icon-btn"
                      type="button"
                      :title="tr('暂停')"
                      :class="{ active: commPaused }"
                      @click="toggleCommPaused"
                    >
                      <span class="material-symbols-outlined">pause_circle</span>
                    </button>
                    <button class="icon-btn" type="button" :title="tr('导出')" @click="exportCommLogs">
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
                  <button :class="{ active: logTab === 'all' }" @click="logTab = 'all'">{{ tr('全部日志') }}</button>
                  <button :class="{ active: logTab === 'uart' }" @click="logTab = 'uart'">{{ tr('串口 (UART)') }}</button>
                  <button :class="{ active: logTab === 'tcp' }" @click="logTab = 'tcp'">{{ tr('网络 (TCP)') }}</button>
                  <div class="search">
                    <span class="material-symbols-outlined">search</span>
                    <input v-model="logKeyword" type="text" :placeholder="tr('过滤日志...')" />
                  </div>
                </div>
                <LogStream
                  compact
                  :items="renderedVisibleCommLogs"
                  :formatTime="formatTime"
                  :formatPayload="formatPayload"
                />
                <div class="panel-footer">
                  <span>{{ visibleCommLogs.length }} {{ tr('条日志记录') }}</span>
                  <button class="link-btn" type="button" @click="clearCommLogs">{{ tr('清除日志') }}</button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="quickDialogOpen" class="modal-backdrop">
            <div class="quick-modal">
              <div class="modal-header">
                <div>
                  <h3>{{ quickDialogMode === 'edit' ? tr('快捷指令编辑') : tr('新增快捷指令') }}</h3>
                  <p>{{ quickDialogMode === 'edit' ? tr('编辑或更新现有的快捷调试指令') : tr('创建新的快捷调试指令') }}</p>
                </div>
                <button class="icon-btn" type="button" @click="closeQuickCommandDialog">
                  <span class="material-symbols-outlined">close</span>
                </button>
              </div>
              <div class="modal-body">
                <div class="quick-field">
                  <label>{{ tr('指令名称') }}</label>
                  <input v-model="quickDraft.name" type="text" :placeholder="tr('例如：CMD PING')" />
                </div>

                <div class="quick-field">
                  <div class="quick-field-header">
                    <label>{{ tr('指令内容') }}</label>
                    <div class="quick-mode">
                      <span class="quick-mode-label">{{ tr('格式:') }}</span>
                      <div class="segmented small">
                        <button :class="{ active: quickDraft.mode === 'text' }" @click="quickDraft.mode = 'text'">{{ tr('文本') }}</button>
                        <button :class="{ active: quickDraft.mode === 'hex' }" @click="quickDraft.mode = 'hex'">
                          HEX
                        </button>
                      </div>
                    </div>
                  </div>
                  <textarea
                    v-model="quickDraft.payload"
                    class="quick-textarea"
                    rows="4"
                    :placeholder="tr('输入要发送的指令内容')"
                  ></textarea>
                  <p class="quick-counter">{{ quickPayloadCount }} / {{ quickPayloadLimit }}</p>
                </div>

                <div class="modal-section quick-options">
                  <div class="section-title">{{ tr('发送选项') }}</div>
                  <div class="toggle-row">
                    <label class="check">
                      <input v-model="quickDraft.appendCR" type="checkbox" />
                      <span>{{ tr('添加 CR (\r)') }}</span>
                    </label>
                    <label class="check">
                      <input v-model="quickDraft.appendLF" type="checkbox" />
                      <span>{{ tr('添加 LF (\n)') }}</span>
                    </label>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button class="btn btn-outline" type="button" @click="closeQuickCommandDialog">{{ tr('取消') }}</button>
                <button class="btn btn-primary" type="button" @click="saveQuickCommand">
                  {{ quickDialogMode === 'edit' ? tr('保存修改') : tr('创建指令') }}
                </button>
              </div>
            </div>
          </div>

          <div v-if="quickDeleteOpen" class="modal-backdrop">
            <div class="quick-modal quick-modal-sm">
              <div class="modal-header">
                <div>
                  <h3>{{ tr('删除快捷指令') }}</h3>
                  <p>{{ tr('确认删除该快捷指令，删除后无法恢复。') }}</p>
                </div>
                <button class="icon-btn" type="button" @click="closeQuickDeleteDialog">
                  <span class="material-symbols-outlined">close</span>
                </button>
              </div>
              <div class="modal-body">
                <div class="quick-delete-summary">
                  <span class="material-symbols-outlined">warning</span>
                  <div>
                    <p class="quick-delete-title">{{ quickDeleting?.name || tr('未命名指令') }}</p>
                    <p class="quick-delete-meta">{{ quickDeleting?.mode === 'hex' ? 'HEX' : tr('文本') }}</p>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button class="btn btn-outline" type="button" @click="closeQuickDeleteDialog">{{ tr('取消') }}</button>
                <button class="btn btn-danger" type="button" @click="confirmQuickDelete">{{ tr('确认删除') }}</button>
              </div>
            </div>
          </div>
        </section>


</template>
