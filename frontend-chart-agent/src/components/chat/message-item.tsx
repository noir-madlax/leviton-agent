'use client';

import { ChatMessage } from '@/lib/types';
import { Badge } from '@/components/ui/badge';
import { User, Bot, ChartBar } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MessageItemProps {
  message: ChatMessage;
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user';
  
  return (
    <div className={cn(
      "flex gap-3 max-w-[85%]",
      isUser ? "ml-auto flex-row-reverse" : "mr-auto"
    )}>
      {/* 头像 */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        isUser ? "bg-blue-500 text-white" : "bg-green-500 text-white"
      )}>
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      {/* 消息内容 */}
      <div className={cn(
        "flex flex-col gap-2",
        isUser ? "items-end" : "items-start"
      )}>
        {/* 消息气泡 */}
        <div className={cn(
          "px-4 py-2 rounded-lg max-w-none",
          isUser 
            ? "bg-blue-500 text-white" 
            : "bg-gray-100 text-gray-900 border"
        )}>
          <p className="text-sm whitespace-pre-wrap">
            {message.content}
          </p>
        </div>

        {/* 图表标识（如果有） */}
        {message.chartData && (
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              <ChartBar className="h-3 w-3 mr-1" />
              已生成图表
            </Badge>
          </div>
        )}

        {/* 时间戳 */}
        <span className="text-xs text-muted-foreground">
          {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </span>
      </div>
    </div>
  );
} 