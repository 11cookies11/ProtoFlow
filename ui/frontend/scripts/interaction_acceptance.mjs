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

  if (failures.length) {
    console.error('Frontend interaction acceptance failed:')
    failures.forEach((item) => console.error(`- ${item}`))
    process.exit(1)
  }

  console.log('Frontend interaction acceptance passed.')
}

run()
