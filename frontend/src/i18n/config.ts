import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enTranslations from './locales/en.json';
import zhTranslations from './locales/zh.json';

// 支持的语言列表
export const supportedLngs = ['en', 'zh'];
export const fallbackLng = 'en'; // 兜底语言：英文

// 语言资源
const resources = {
  en: {
    translation: enTranslations
  },
  zh: {
    translation: zhTranslations
  }
};

// i18next配置
i18n
  .use(LanguageDetector) // 浏览器语言检测
  .use(initReactI18next) // React集成
  .init({
    resources,
    supportedLngs,
    fallbackLng,
    
    // 语言检测配置
    detection: {
      // 检测顺序：localStorage -> navigator -> fallback
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'i18nextLng',
      caches: ['localStorage'],
    },

    interpolation: {
      escapeValue: false, // React已经转义了
    },

    // 开发模式下显示调试信息
    debug: process.env.NODE_ENV === 'development',
    
    // SSR支持
    react: {
      useSuspense: false, // 禁用 Suspense 以避免 SSR 问题
    },
  });

export default i18n;

// 语言显示配置
export const languageConfig = {
  en: {
    label: 'English',
    flag: '🇺🇸'
  },
  zh: {
    label: '中文',
    flag: '����'
  }
} as const; 