import { zhCN } from './locales/zhCN'
import { enUS } from './locales/enUS'
import { zhTW } from './locales/zhTW'
import { jaJP } from './locales/jaJP'
import { koKR } from './locales/koKR'
import { frFR } from './locales/frFR'
import { deDE } from './locales/deDE'
import { esES } from './locales/esES'
import { ptBR } from './locales/ptBR'
import { ruRU } from './locales/ruRU'
import { ar } from './locales/ar'
import { hi } from './locales/hi'
import { itIT } from './locales/itIT'
import { nlNL } from './locales/nlNL'
import { thTH } from './locales/thTH'
import { viVN } from './locales/viVN'
import { idID } from './locales/idID'
import { trTR } from './locales/trTR'
import { plPL } from './locales/plPL'
import { ukUA } from './locales/ukUA'

export const translations = {
  'zh-CN': zhCN,
  'zh-TW': zhTW,
  'en-US': enUS,
  'ja-JP': jaJP,
  'ko-KR': koKR,
  'fr-FR': frFR,
  'de-DE': deDE,
  'es-ES': esES,
  'pt-BR': ptBR,
  'ru-RU': ruRU,
  ar,
  hi,
  'it-IT': itIT,
  'nl-NL': nlNL,
  'th-TH': thTH,
  'vi-VN': viVN,
  'id-ID': idID,
  'tr-TR': trTR,
  'pl-PL': plPL,
  'uk-UA': ukUA,
} as const

export const supportedLanguages = new Set(Object.keys(translations))

export const DEFAULT_LANGUAGE = 'zh-CN'
