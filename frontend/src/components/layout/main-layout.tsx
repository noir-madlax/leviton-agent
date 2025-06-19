'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { ChatInterface } from '@/components/chat/chat-interface';
import { ChartRenderer } from '@/components/charts/chart-renderer';
import { DataImportTab } from '@/components/tabs/data-import-tab';
import { DataConfirmationTab } from '@/components/tabs/data-confirmation-tab';
import { AnalysisTab } from '@/components/tabs/analysis-tab';
import { AnalysisDbTab } from '@/components/tabs/analysis-db-tab';

export function MainLayout() {
  const [leftPanelWidth, setLeftPanelWidth] = useState(50); // 百分比
  const [activeTab, setActiveTab] = useState('step1');
  const [assignmentName, setAssignmentName] = useState('');

  const handleNavigateToAnalysis = (name: string) => {
    setAssignmentName(name);
    setActiveTab('step3-db');
  };

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
    <div className="h-screen flex flex-col overflow-hidden bg-background">
      {/* 顶部Tab导航 */}
      <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-2">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="step1" className="text-sm">
                Step 1: Data Import
              </TabsTrigger>
              <TabsTrigger value="step2" className="text-sm">
                Step 2: Data Confirmation
              </TabsTrigger>
              <TabsTrigger value="step3-db" className="text-xs">
                {assignmentName ? (
                  <>Step 3: Analysis<br/>{assignmentName}</>
                ) : (
                  <>Step 3: Analysis<br/>by DB</>
                )}
              </TabsTrigger>
              <TabsTrigger value="step4" className="text-sm">
                Step 4: Chat
              </TabsTrigger>
              <TabsTrigger value="step3" className="text-xs">
                Old Analysis<br/>by File
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </div>

      {/* 主内容区域 */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
          {/* Step 1: 数据导入 */}
          <TabsContent value="step1" className="h-full m-0">
            <div className="h-full p-4">
              <DataImportTab />
            </div>
          </TabsContent>

          {/* Step 2: 数据确认 */}
          <TabsContent value="step2" className="h-full m-0">
            <div className="h-full p-4">
              <DataConfirmationTab onNavigateToAnalysis={handleNavigateToAnalysis} />
            </div>
          </TabsContent>

          {/* Step 3: 分析 (文件版本) */}
          <TabsContent value="step3" className="h-full m-0">
            <div className="h-full p-4">
              <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-4">
                <div className="flex">
                  <div className="ml-3">
                    <p className="text-sm text-green-700">
                      <strong>文件版本:</strong> 此版本使用静态文件数据
                    </p>
                  </div>
                </div>
              </div>
              <AnalysisTab />
            </div>
          </TabsContent>

          {/* Step 3: 分析 (数据库版本) */}
          <TabsContent value="step3-db" className="h-full m-0">
            <div className="h-full p-4">
              <AnalysisDbTab />
            </div>
          </TabsContent>

          {/* Step 4: 聊天 (原有功能) */}
          <TabsContent value="step4" className="h-full m-0">
            <div className="h-full flex overflow-hidden">
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
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
} 