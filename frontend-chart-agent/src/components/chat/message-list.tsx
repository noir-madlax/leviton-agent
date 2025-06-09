'use client';

import { ChatMessage } from '@/lib/types';
import { MessageItem } from './message-item';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.length === 0 && !isLoading ? (
        <div className="text-center text-muted-foreground py-8">
          <p className="text-lg mb-2">👋 欢迎使用 AI 数据分析助手</p>
          <p className="text-sm">
            问我关于数据的任何问题，我会为您生成相应的图表来可视化展示
          </p>
          <div className="mt-4 text-xs">
            <p>💡 示例问题：</p>
            <ul className="mt-2 space-y-1">
              <li>• "显示最近6个月的销售趋势"</li>
              <li>• "对比各产品的销售表现"</li>
              <li>• "分析用户增长情况"</li>
            </ul>
          </div>
        </div>
      ) : (
        messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))
      )}
      
      {isLoading && (
        <div className="flex items-center gap-2 text-muted-foreground">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
          <span className="text-sm">AI 正在分析数据并生成图表...</span>
        </div>
      )}
    </div>
  );
} 