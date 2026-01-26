import yaml from 'js-yaml'

export type YamlParseError = {
  message: string
  line?: number
  column?: number
}

export function parseYamlUI(yamlText: string):
  | { ok: true; value: unknown }
  | { ok: false; error: YamlParseError } {
  try {
    const value = yaml.load(yamlText)
    return { ok: true, value }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'YAML parse error'
    const mark = (error as { mark?: { line?: number; column?: number } }).mark
    const line = typeof mark?.line === 'number' ? mark.line + 1 : undefined
    const column = typeof mark?.column === 'number' ? mark.column + 1 : undefined
    return { ok: false, error: { message, line, column } }
  }
}
