# ProtoFlow i18n Manual (es-ES)

Language Index: [zh-CN](I18N_MANUAL.zh-CN.md) | [en-US](I18N_MANUAL.en-US.md) | [zh-TW](I18N_MANUAL.zh-TW.md) | [ja-JP](I18N_MANUAL.ja-JP.md) | [ko-KR](I18N_MANUAL.ko-KR.md) | [fr-FR](I18N_MANUAL.fr-FR.md) | [de-DE](I18N_MANUAL.de-DE.md) | **es-ES** | [pt-BR](I18N_MANUAL.pt-BR.md) | [ru-RU](I18N_MANUAL.ru-RU.md) | [ar](I18N_MANUAL.ar.md) | [hi](I18N_MANUAL.hi.md) | [it-IT](I18N_MANUAL.it-IT.md) | [nl-NL](I18N_MANUAL.nl-NL.md) | [th-TH](I18N_MANUAL.th-TH.md) | [vi-VN](I18N_MANUAL.vi-VN.md) | [id-ID](I18N_MANUAL.id-ID.md) | [tr-TR](I18N_MANUAL.tr-TR.md) | [pl-PL](I18N_MANUAL.pl-PL.md) | [uk-UA](I18N_MANUAL.uk-UA.md)

Current Language: **Spanish**

## 1. Source of Truth

- Aggregator: `ui/frontend/src/i18n/index.ts`
- Locale dictionaries: `ui/frontend/src/i18n/locales/*.ts`
- Default locale: `zh-CN`

## 2. Locale Map

| Locale | Locale File |
|---|---|
| `zh-CN` | ui/frontend/src/i18n/locales/zhCN.ts |
| `en-US` | ui/frontend/src/i18n/locales/enUS.ts |
| `zh-TW` | ui/frontend/src/i18n/locales/zhTW.ts |
| `ja-JP` | ui/frontend/src/i18n/locales/jaJP.ts |
| `ko-KR` | ui/frontend/src/i18n/locales/koKR.ts |
| `fr-FR` | ui/frontend/src/i18n/locales/frFR.ts |
| `de-DE` | ui/frontend/src/i18n/locales/deDE.ts |
| `es-ES` | ui/frontend/src/i18n/locales/esES.ts |
| `pt-BR` | ui/frontend/src/i18n/locales/ptBR.ts |
| `ru-RU` | ui/frontend/src/i18n/locales/ruRU.ts |
| `ar` | ui/frontend/src/i18n/locales/ar.ts |
| `hi` | ui/frontend/src/i18n/locales/hi.ts |
| `it-IT` | ui/frontend/src/i18n/locales/itIT.ts |
| `nl-NL` | ui/frontend/src/i18n/locales/nlNL.ts |
| `th-TH` | ui/frontend/src/i18n/locales/thTH.ts |
| `vi-VN` | ui/frontend/src/i18n/locales/viVN.ts |
| `id-ID` | ui/frontend/src/i18n/locales/idID.ts |
| `tr-TR` | ui/frontend/src/i18n/locales/trTR.ts |
| `pl-PL` | ui/frontend/src/i18n/locales/plPL.ts |
| `uk-UA` | ui/frontend/src/i18n/locales/ukUA.ts |

## 3. Resolution Order

1. `translations[selectedLocale][key]`
2. `translations[DEFAULT_LANGUAGE][key]`
3. Inline fallback text passed to `t(key, fallback)`
4. Final fallback to the key string itself

## 4. Add or Update a Language

1. Create or update locale file in `ui/frontend/src/i18n/locales/`.
2. Export locale object and import it in `ui/frontend/src/i18n/index.ts`.
3. Add locale code to `translations` map.
4. Verify language switch in Settings page.
5. Run frontend build and smoke-check docs button text visibility.

## 5. Required Key Groups

- `nav.*`
- `header.*`
- `action.*`
- `status.*` and `filter.*`
- `settings.*`

## 6. QA Checklist

- No missing labels on primary pages (Manual/Scripts/Protocols/Settings).
- No mojibake in locale files.
- `npm --prefix ui/frontend run build` passes.
- Settings docs button has icon and visible text.

## 7. Related Documents

- [User Guide (ZH)](../USER_GUIDE.md)
- [User Guide (EN)](../USER_GUIDE_EN.md)

Language Index: [zh-CN](I18N_MANUAL.zh-CN.md) | [en-US](I18N_MANUAL.en-US.md) | [zh-TW](I18N_MANUAL.zh-TW.md) | [ja-JP](I18N_MANUAL.ja-JP.md) | [ko-KR](I18N_MANUAL.ko-KR.md) | [fr-FR](I18N_MANUAL.fr-FR.md) | [de-DE](I18N_MANUAL.de-DE.md) | **es-ES** | [pt-BR](I18N_MANUAL.pt-BR.md) | [ru-RU](I18N_MANUAL.ru-RU.md) | [ar](I18N_MANUAL.ar.md) | [hi](I18N_MANUAL.hi.md) | [it-IT](I18N_MANUAL.it-IT.md) | [nl-NL](I18N_MANUAL.nl-NL.md) | [th-TH](I18N_MANUAL.th-TH.md) | [vi-VN](I18N_MANUAL.vi-VN.md) | [id-ID](I18N_MANUAL.id-ID.md) | [tr-TR](I18N_MANUAL.tr-TR.md) | [pl-PL](I18N_MANUAL.pl-PL.md) | [uk-UA](I18N_MANUAL.uk-UA.md)