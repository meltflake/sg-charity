import { ui } from './ui';

export type Lang = 'en' | 'zh';
export type UIKey = keyof typeof ui.en;

export function t(key: UIKey, lang: Lang): string {
  return ui[lang]?.[key] ?? ui.en[key] ?? key;
}

export function tVar(key: UIKey, lang: Lang, vars: Record<string, string | number>): string {
  let text = t(key, lang);
  for (const [k, v] of Object.entries(vars)) {
    text = text.replaceAll(`{${k}}`, String(v));
  }
  return text;
}

// Shorthand: returns both en and zh for data-i18n attributes
export function i18n(key: UIKey): { 'data-i18n': true; 'data-en': string; 'data-zh': string } {
  return { 'data-i18n': true, 'data-en': t(key, 'en'), 'data-zh': t(key, 'zh') };
}

export function i18nVar(key: UIKey, vars: Record<string, string | number>): { 'data-i18n': true; 'data-en': string; 'data-zh': string } {
  return { 'data-i18n': true, 'data-en': tVar(key, 'en', vars), 'data-zh': tVar(key, 'zh', vars) };
}
