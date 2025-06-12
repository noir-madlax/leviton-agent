'use client';

import { useState } from 'react';

import { ChatInterface } from '@/components/chat/chat-interface';
import { ChartRenderer } from '@/components/charts/chart-renderer';

export function MainLayout() {
  const [leftPanelWidth, setLeftPanelWidth] = useState(50); // 百分比

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    
    const startX = e.clientX;
    const startWidth = leftPanelWidth;
    const containerWidth = window.innerWidth;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - startX;
      const deltaWidthPercent = (deltaX / containerWidth) * 100;
      const newWidth = Math.min(Math.max(startWidth + deltaWidthPercent, 25), 75);
      setLeftPanelWidth(newWidth);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      {/* 左侧聊天面板 */}
      <div 
        className="flex-shrink-0 flex flex-col"
        style={{ width: `${leftPanelWidth}%` }}
      >
        <div className="h-full p-4">
          <ChatInterface />
        </div>
      </div>

      {/* 分割线 */}
      <div 
        className="flex-shrink-0 flex items-center justify-center w-1 bg-border hover:bg-border/80 cursor-col-resize transition-colors"
        onMouseDown={handleMouseDown}
      >
        <div className="w-0.5 h-8 bg-border rounded-full" />
      </div>

      {/* 右侧图表面板 */}
      <div 
        className="flex-1 flex flex-col min-w-0"
        style={{ width: `${100 - leftPanelWidth}%` }}
      >
        <div className="h-full p-4">
          <ChartRenderer />
        </div>
      </div>
    </div>
  );
} 