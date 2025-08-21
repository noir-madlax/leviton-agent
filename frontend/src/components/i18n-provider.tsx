'use client';

import { useEffect, useState } from 'react';

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // 动态导入i18n配置
    import('@/i18n/config').then(() => {
      setIsInitialized(true);
    });
  }, []);

  // 在i18n初始化之前显示加载状态
  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return <>{children}</>;
} 