import fs from 'node:fs'
import path from 'node:path'
import { gzipSync } from 'node:zlib'

const root = process.cwd()
const distDir = path.join(root, 'dist', 'assets')
const budgetPath = path.join(root, 'config', 'perf_budget.json')

function kb(bytes) {
  return bytes / 1024
}

function listAssets() {
  if (!fs.existsSync(distDir)) {
    throw new Error('dist/assets not found. Run npm run build first.')
  }
  const files = fs.readdirSync(distDir)
  return files
}

function sumByExt(files, ext) {
  const selected = files.filter((name) => name.endsWith(ext))
  let raw = 0
  let gz = 0
  for (const name of selected) {
    const full = path.join(distDir, name)
    const buf = fs.readFileSync(full)
    raw += buf.length
    gz += gzipSync(buf).length
  }
  return { files: selected, raw, gz }
}

function loadBudget() {
  if (!fs.existsSync(budgetPath)) {
    throw new Error('Budget file not found: config/perf_budget.json')
  }
  return JSON.parse(fs.readFileSync(budgetPath, 'utf8'))
}

function printLine(label, value, max) {
  const status = value <= max ? 'OK' : 'FAIL'
  console.log(`${status.padEnd(4)} ${label.padEnd(22)} ${value.toFixed(2)} KB / budget ${max.toFixed(2)} KB`)
  return status === 'OK'
}

try {
  const files = listAssets()
  const budget = loadBudget()
  const js = sumByExt(files, '.js')
  const css = sumByExt(files, '.css')

  const jsRawKb = kb(js.raw)
  const cssRawKb = kb(css.raw)
  const jsGzipKb = kb(js.gz)
  const cssGzipKb = kb(css.gz)

  console.log('Frontend Performance Budget Report')
  console.log(`Assets directory: ${distDir}`)
  console.log(`JS files: ${js.files.length}, CSS files: ${css.files.length}`)

  const ok = [
    printLine('JS raw bundle', jsRawKb, budget.js_bundle_max_kb),
    printLine('CSS raw bundle', cssRawKb, budget.css_bundle_max_kb),
    printLine('JS gzip bundle', jsGzipKb, budget.js_gzip_max_kb),
    printLine('CSS gzip bundle', cssGzipKb, budget.css_gzip_max_kb),
  ].every(Boolean)

  if (!ok) {
    console.error('\nPerformance budget exceeded.')
    process.exit(1)
  }

  console.log('\nAll bundle budgets satisfied.')
} catch (error) {
  console.error(String(error instanceof Error ? error.message : error))
  process.exit(1)
}
