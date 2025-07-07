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
          <p className="text-lg mb-2">👋 Welcome to AI Data Analysis Assistant</p>
          <p className="text-sm">
            Ask me any questions about your data, and I'll generate corresponding charts for visualization
          </p>
          <div className="mt-4 text-xs">
            <p>💡 Example Questions:</p>
            <ul className="mt-2 space-y-1">
              <li>• &ldquo;Show the sales trends for the last 6 months&rdquo;</li>
              <li>• &ldquo;Compare the sales performance of each product&rdquo;</li>
              <li>• &ldquo;Analyze user growth trends&rdquo;</li>
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
          <span className="text-sm">AI is analyzing data and generating charts...</span>
        </div>
      )}
    </div>
  );
} 