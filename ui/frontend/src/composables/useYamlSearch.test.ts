import { afterEach, describe, expect, it, vi } from 'vitest'
import { useYamlSearch } from './useYamlSearch'

const originalPrompt = window.prompt
const originalFind = window.find

afterEach(() => {
  window.prompt = originalPrompt
  window.find = originalFind
})

describe('useYamlSearch', () => {
  it('dispatches selection when keyword found in editor', () => {
    const dispatch = vi.fn()
    window.prompt = vi.fn(() => 'abc')
    const search = useYamlSearch({
      tr: (text) => text,
      addScriptLog: () => {},
      getEditor: () => ({
        state: {
          doc: {
            toString: () => 'xxx ABC yyy',
          },
        },
        dispatch,
      }),
    })

    search.searchYaml()
    expect(dispatch).toHaveBeenCalled()
  })

  it('logs not found when editor exists but no match', () => {
    const logs: string[] = []
    window.prompt = vi.fn(() => 'needle')
    const search = useYamlSearch({
      tr: (text) => text,
      addScriptLog: (line) => logs.push(line),
      getEditor: () => ({
        state: {
          doc: {
            toString: () => 'haystack',
          },
        },
        dispatch: () => {},
      }),
    })

    search.searchYaml()
    expect(logs).toContain('[INFO] Not found: needle')
  })

  it('falls back to window.find when editor missing', () => {
    const logs: string[] = []
    window.prompt = vi.fn(() => 'x')
    window.find = vi.fn(() => false)
    const search = useYamlSearch({
      tr: (text) => text,
      addScriptLog: (line) => logs.push(line),
      getEditor: () => null,
    })

    search.searchYaml()
    expect(window.find).toHaveBeenCalledWith('x')
    expect(logs).toContain('[INFO] Not found: x')
  })
})
