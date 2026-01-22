<script setup>
import { inject } from 'vue'
import LogStream from './LogStream.vue'

const bindings = inject('scriptsView')
if (!bindings) {
  throw new Error('scriptsView bindings not provided')
}

const {
  scriptFileName,
  scriptFilePath,
  loadYaml,
  saveYaml,
  yamlFileInputRef,
  handleYamlFile,
  yamlCollapsed,
  toggleYamlCollapsed,
  copyYaml,
  searchYaml,
  yamlEditorRef,
  scriptStatusClass,
  scriptRunning,
  scriptStatusLabel,
  scriptCanRun,
  scriptCanStop,
  runScript,
  stopScript,
  scriptState,
  scriptStepIndex,
  scriptStepTotal,
  scriptProgress,
  scriptElapsedLabel,
  scriptErrorCount,
  scriptVariables,
  refreshScriptVariables,
  clearScriptLogs,
  scrollScriptLogsToBottom,
  renderedScriptLogs,
  scriptLogRef,
} = bindings
</script>

<template>
  <section class="page">
          <header class="page-header spaced scripts-header">
            <div>
              <h2 class="scripts-title">
                自动脚本
                <span class="chip">{{ scriptFileName }}</span>
                <span class="badge">只读</span>
              </h2>
              <p class="scripts-path">{{ scriptFilePath }}</p>
            </div>
            <div class="header-actions">
              <button class="btn btn-outline" @click="loadYaml">
                <span class="material-symbols-outlined">folder_open</span>
                加载脚本
              </button>
              <button class="btn btn-outline" @click="saveYaml">
                <span class="material-symbols-outlined">save</span>
                保存
              </button>
            </div>
            <input
              ref="yamlFileInputRef"
              type="file"
              accept=".yaml,.yml,text/yaml"
              style="display: none"
              @change="handleYamlFile"
            />
          </header>

          <div class="scripts-grid">
            <div class="panel editor">
              <div class="panel-title bar">
                <span class="material-symbols-outlined">code</span>
                DSL 编辑器
                <div class="panel-actions">
                  <button class="icon-btn" :title="yamlCollapsed ? '灞曞紑' : '鏀惰捣'" @click="toggleYamlCollapsed">
                    <span class="material-symbols-outlined">
                      {{ yamlCollapsed ? 'unfold_more' : 'unfold_less' }}
                    </span>
                  </button>
                  <button class="icon-btn" title="复制" @click="copyYaml">
                    <span class="material-symbols-outlined">content_copy</span>
                  </button>
                  <button class="icon-btn" title="搜索" @click="searchYaml">
                    <span class="material-symbols-outlined">search</span>
                  </button>
                </div>
              </div>
              <div ref="yamlEditorRef" class="code-area" :class="{ collapsed: yamlCollapsed }"></div>
            </div>

            <div class="scripts-side">
              <div class="panel stack">
                <div class="panel-title simple">执行控制</div>
                <div class="status-pill" :class="scriptStatusClass">
                  <span v-if="scriptRunning" class="pulse"></span>
                  {{ scriptStatusLabel }}
                </div>
                <div class="button-grid">
                  <button
                    class="btn btn-primary"
                    :class="{ 'btn-muted': !scriptCanRun }"
                    :disabled="!scriptCanRun"
                    @click="runScript"
                  >
                    <span class="material-symbols-outlined">play_arrow</span>
                    运行
                  </button>
                  <button
                    class="btn btn-danger"
                    :class="{ 'btn-muted': !scriptCanStop }"
                    :disabled="!scriptCanStop"
                    @click="stopScript"
                  >
                    <span class="material-symbols-outlined">stop</span>
                    停止
                  </button>
                </div>
                <div class="progress-block">
                  <div class="progress-row">
                    <span>当前步骤: <strong>{{ scriptState }}</strong></span>
                    <span class="mono">{{ scriptStepIndex }}/{{ scriptStepTotal }}</span>
                  </div>
                  <div class="progress-bar">
                    <div class="progress" :style="{ width: `${Math.min(100, scriptProgress)}%` }"></div>
                  </div>
                  <div class="progress-stats">
                    <div>
                      <span>已用时间</span>
                      <strong class="mono">{{ scriptElapsedLabel }}</strong>
                    </div>
                    <div>
                      <span>错误数</span>
                      <strong class="mono">{{ scriptErrorCount }}</strong>
                    </div>
                  </div>
                </div>
              </div>

              <div class="panel stack">
                <div class="panel-title simple">
                  变量监控
                  <button class="link-btn" type="button" @click="refreshScriptVariables">刷新</button>
                </div>
                <table class="mini-table">
                  <thead>
                    <tr>
                      <th>变量名</th>
                      <th class="right">当前值</th>
                    </tr>
                  </thead>
                  <tbody v-if="scriptVariables.length">
                    <tr v-for="item in scriptVariables" :key="item.name">
                      <td>{{ item.name }}</td>
                      <td class="right">{{ item.value || '--' }}</td>
                    </tr>
                  </tbody>
                  <tbody v-else>
                    <tr>
                      <td colspan="2" class="right">--</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div class="panel log-panel">
            <div class="panel-title bar">
              <span class="material-symbols-outlined">terminal</span>
              运行日志
              <div class="panel-actions">
                <button class="icon-btn" title="清空日志" @click="clearScriptLogs">
                  <span class="material-symbols-outlined">block</span>
                </button>
                <button class="icon-btn" title="滚动到底部" @click="scrollScriptLogsToBottom">
                  <span class="material-symbols-outlined">vertical_align_bottom</span>
                </button>
              </div>
            </div>
            <LogStream ref="scriptLogRef" compact mode="text" :items="renderedScriptLogs" />
          </div>
        </section>

        
</template>
