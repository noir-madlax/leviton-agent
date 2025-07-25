import { useTranslation } from 'react-i18next';

// 通用翻译Hook - 最常用
export function useCommonT() {
  const { t } = useTranslation();
  return (key: string) => t(`common.${key}`);
}

// 认证翻译Hook
export function useAuthT() {
  const { t } = useTranslation();
  return (key: string) => t(`auth.${key}`);
}

// 导航翻译Hook
export function useNavT() {
  const { t } = useTranslation();
  return (key: string) => t(`navigation.${key}`);
}

// 项目翻译Hook
export function useProjectT() {
  const { t } = useTranslation();
  return (key: string) => t(`project.${key}`);
}

// 仪表板翻译Hook
export function useDashboardT() {
  const { t } = useTranslation();
  return (key: string) => t(`dashboard.${key}`);
}

// 图表翻译Hook
export function useChartsT() {
  const { t } = useTranslation();
  return (key: string) => t(`charts.${key}`);
}

// 筛选器翻译Hook
export function useFiltersT() {
  const { t } = useTranslation();
  return (key: string) => t(`filters.${key}`);
}

// 错误翻译Hook
export function useErrorsT() {
  const { t } = useTranslation();
  return (key: string) => t(`errors.${key}`);
}

// 元数据翻译Hook
export function useMetaT() {
  const { t } = useTranslation();
  return (key: string) => t(`meta.${key}`);
}

// 通用翻译Hook - 完整版本
export function useT() {
  const { t } = useTranslation();
  return t;
} 