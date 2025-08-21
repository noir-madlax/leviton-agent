import type en from './locales/en.json';

// 翻译资源类型
export type TranslationResource = typeof en;

// 支持的语言类型
export type SupportedLanguage = 'en' | 'zh';

// 翻译键路径类型
export type TranslationKey = keyof typeof en;

// 嵌套翻译键类型
export type NestedTranslationKeys<T> = T extends string
  ? T
  : T extends object
  ? {
      [K in keyof T]: K extends string
        ? T[K] extends string
          ? K
          : T[K] extends object
          ? `${K}.${NestedTranslationKeys<T[K]>}`
          : never
        : never;
    }[keyof T]
  : never;

// 完整翻译键类型
export type FullTranslationKey = NestedTranslationKeys<typeof en>;

// 语言配置类型
export interface LanguageConfig {
  label: string;
  flag: string;
}

// react-i18next 模块声明
declare module 'react-i18next' {
  interface CustomTypeOptions {
    defaultNS: 'translation';
    resources: {
      translation: typeof en;
    };
  }
} 