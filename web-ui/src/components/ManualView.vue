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
  sendPayload,
  sendQuickCommand,
} = bindings
</script>

<template>
  <section class="page">
          <header class="page-header">
            <div>
              <h2>串口终端</h2>
              <p>传统串口调试工具：发送命令、监听 I/O 与日志回显。</p>
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
                  <button class="icon-btn" type="button" title="新增快捷指令" @click="addQuickCommand">
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
                      <span class="quick-meta">{{ cmd.mode === 'hex' ? 'HEX' : '文本' }}</span>
                    </div>
                    <div class="quick-item-actions">
                      <button class="icon-btn small" type="button" title="编辑" @click.stop="editQuickCommand(cmd)">
                        <span class="material-symbols-outlined">edit</span>
                      </button>
                      <button class="icon-btn small" type="button" title="删除" @click.stop="openQuickDeleteDialog(cmd)">
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
                    <button class="icon-btn" type="button" title="清除" @click="clearCommLogs">
                      <span class="material-symbols-outlined">delete</span>
                    </button>
                    <button
                      class="icon-btn"
                      type="button"
                      title="暂停"
                      :class="{ active: commPaused }"
                      @click="toggleCommPaused"
                    >
                      <span class="material-symbols-outlined">pause_circle</span>
                    </button>
                    <button class="icon-btn" type="button" title="导出" @click="exportCommLogs">
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

          <div v-if="quickDialogOpen" class="modal-backdrop">
            <div class="quick-modal">
              <div class="modal-header">
                <div>
                  <h3>{{ quickDialogMode === 'edit' ? '快捷指令编辑' : '新增快捷指令' }}</h3>
                  <p>{{ quickDialogMode === 'edit' ? '编辑或更新现有的快捷调试指令' : '创建新的快捷调试指令' }}</p>
                </div>
                <button class="icon-btn" type="button" @click="closeQuickCommandDialog">
                  <span class="material-symbols-outlined">close</span>
                </button>
              </div>
              <div class="modal-body">
                <div class="quick-field">
                  <label>指令名称</label>
                  <input v-model="quickDraft.name" type="text" placeholder="例如：CMD PING" />
                </div>

                <div class="quick-field">
                  <div class="quick-field-header">
                    <label>指令内容</label>
                    <div class="quick-mode">
                      <span class="quick-mode-label">格式:</span>
                      <div class="segmented small">
                        <button :class="{ active: quickDraft.mode === 'text' }" @click="quickDraft.mode = 'text'">
                          文本
                        </button>
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
                    placeholder="输入要发送的指令内容"
                  ></textarea>
                  <p class="quick-counter">{{ quickPayloadCount }} / {{ quickPayloadLimit }}</p>
                </div>

                <div class="modal-section quick-options">
                  <div class="section-title">发送选项</div>
                  <div class="toggle-row">
                    <label class="check">
                      <input v-model="quickDraft.appendCR" type="checkbox" />
                      <span>添加 CR (\r)</span>
                    </label>
                    <label class="check">
                      <input v-model="quickDraft.appendLF" type="checkbox" />
                      <span>添加 LF (\n)</span>
                    </label>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button class="btn btn-outline" type="button" @click="closeQuickCommandDialog">取消</button>
                <button class="btn btn-primary" type="button" @click="saveQuickCommand">
                  {{ quickDialogMode === 'edit' ? '保存修改' : '创建指令' }}
                </button>
              </div>
            </div>
          </div>

          <div v-if="quickDeleteOpen" class="modal-backdrop">
            <div class="quick-modal quick-modal-sm">
              <div class="modal-header">
                <div>
                  <h3>删除快捷指令</h3>
                  <p>确认删除该快捷指令，删除后无法恢复。</p>
                </div>
                <button class="icon-btn" type="button" @click="closeQuickDeleteDialog">
                  <span class="material-symbols-outlined">close</span>
                </button>
              </div>
              <div class="modal-body">
                <div class="quick-delete-summary">
                  <span class="material-symbols-outlined">warning</span>
                  <div>
                    <p class="quick-delete-title">{{ quickDeleting?.name || '未命名指令' }}</p>
                    <p class="quick-delete-meta">{{ quickDeleting?.mode === 'hex' ? 'HEX' : '文本' }}</p>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button class="btn btn-outline" type="button" @click="closeQuickDeleteDialog">取消</button>
                <button class="btn btn-danger" type="button" @click="confirmQuickDelete">确认删除</button>
              </div>
            </div>
          </div>
        </section>


</template>
