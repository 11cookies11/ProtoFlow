import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()

function read(file) {
  const full = path.join(root, file)
  if (!fs.existsSync(full)) {
    throw new Error(`Missing file: ${file}`)
  }
  return fs.readFileSync(full, 'utf8')
}

function expectIncludes(content, needle, label, failures) {
  if (!content.includes(needle)) {
    failures.push(`${label}: missing "${needle}"`)
  }
}

function listVueFiles(dir, output = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.name === 'ui-kit') continue
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      listVueFiles(full, output)
      continue
    }
    if (entry.isFile() && entry.name.endsWith('.vue')) {
      output.push(full)
    }
  }
  return output
}

function auditButtonsWithoutInteraction(failures) {
  const componentsRoot = path.join(root, 'src', 'components')
  const files = listVueFiles(componentsRoot)
  const ignoredNames = new Set(['HelloWorld.vue'])
  const buttonPattern = /<button\b[\s\S]*?>/g
  for (const file of files) {
    if (ignoredNames.has(path.basename(file))) continue
    const content = fs.readFileSync(file, 'utf8')
    const buttons = content.match(buttonPattern) || []
    for (const tag of buttons) {
      const hasClick = /@click|v-on:click/.test(tag)
      const isDisabled = /\bdisabled\b|:disabled=/.test(tag)
      const isSubmit = /type="submit"|type='submit'/.test(tag)
      if (hasClick || isDisabled || isSubmit) continue
      const rel = path.relative(root, file).replace(/\\/g, '/')
      failures.push(`Button interaction audit: ${rel} has clickable-looking button without @click/disabled`)
    }
  }
}

function run() {
  const failures = []

  const toolbar = read('src/components/proxy/ProxyCaptureToolbar.vue')
  expectIncludes(toolbar, "defineEmits(['update:search-keyword', 'resume-capture', 'open-settings'])", 'ProxyCaptureToolbar emits', failures)

  const footer = read('src/components/proxy/ProxyCaptureFooter.vue')
  expectIncludes(footer, "defineEmits(['page-first', 'page-prev', 'page-next', 'page-last', 'export'])", 'ProxyCaptureFooter emits', failures)

  const details = read('src/components/proxy/ProxyCaptureDetails.vue')
  expectIncludes(details, "defineEmits(['close', 'copy-hex', 'open-rule'])", 'ProxyCaptureDetails emits', failures)

  const monitor = read('src/components/ProxyMonitorView.vue')
  expectIncludes(monitor, '@update:search-keyword="captureSearchKeyword = $event"', 'ProxyMonitorView toolbar binding', failures)
  expectIncludes(monitor, '@resume-capture="resumeCapture"', 'ProxyMonitorView resume binding', failures)
  expectIncludes(monitor, '@open-settings="openCaptureRule"', 'ProxyMonitorView settings binding', failures)
  expectIncludes(monitor, '@page-first="scrollCaptureToPage(1)"', 'ProxyMonitorView footer first page binding', failures)
  expectIncludes(monitor, '@page-last="scrollCaptureToPage(captureMetaView.pageCount)"', 'ProxyMonitorView footer last page binding', failures)
  expectIncludes(monitor, '@copy-hex="copyActiveHex"', 'ProxyMonitorView details copy binding', failures)
  expectIncludes(monitor, '@open-rule="openCaptureRule"', 'ProxyMonitorView details rule binding', failures)

  const matrix = read('../../docs/FRONTEND_INTERACTION_TEST_MATRIX.md')
  expectIncludes(matrix, 'Search keyword filters frame rows by id/protocol/summary/raw hex', 'Interaction matrix coverage', failures)
  expectIncludes(matrix, 'Capture footer pagination buttons (`first/prev/next/last`) are actionable', 'Interaction matrix pagination coverage', failures)
  auditButtonsWithoutInteraction(failures)

  if (failures.length) {
    console.error('Frontend interaction acceptance failed:')
    failures.forEach((item) => console.error(`- ${item}`))
    process.exit(1)
  }

  console.log('Frontend interaction acceptance passed.')
}

run()
