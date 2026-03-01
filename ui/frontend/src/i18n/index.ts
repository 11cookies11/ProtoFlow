import { zhCN } from './locales/zhCN'
import { enUS } from './locales/enUS'

export const translations = {
  'zh-CN': zhCN,
  'zh-TW': enUS,
  'en-US': enUS,
  'ja-JP': enUS,
  'ko-KR': enUS,
  'fr-FR': enUS,
  'de-DE': enUS,
  'es-ES': enUS,
  'pt-BR': enUS,
  'ru-RU': enUS,
  ar: enUS,
  hi: enUS,
  'it-IT': enUS,
  'nl-NL': enUS,
  'th-TH': enUS,
  'vi-VN': enUS,
  'id-ID': enUS,
  'tr-TR': enUS,
  'pl-PL': enUS,
  'uk-UA': enUS,
} as const

export const supportedLanguages = new Set(Object.keys(translations))

export const DEFAULT_LANGUAGE = 'zh-CN'
