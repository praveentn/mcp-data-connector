import { useChat } from '../../hooks/useChat'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { MessageSquare } from 'lucide-react'

export function ChatPanel() {
  const { messages, isLoading, sendMessage } = useChat()

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
        <MessageSquare className="w-4 h-4 text-blue-400" />
        <span className="text-sm font-medium text-gray-300">Conversational Agent</span>
      </div>

      <MessageList messages={messages} isLoading={isLoading} />

      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  )
}
