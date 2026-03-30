import { useEffect, useRef } from 'react'
import type { Message } from '../../types/chat'
import { MessageBubble } from './MessageBubble'
import { Loader2 } from 'lucide-react'

interface Props {
  messages: Message[]
  isLoading: boolean
}

export function MessageList({ messages, isLoading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <div className="text-4xl mb-4">🔌</div>
        <h2 className="text-xl font-semibold text-gray-300 mb-2">MCP Data Connector</h2>
        <p className="text-gray-500 text-sm max-w-sm">
          Ask me to query your sales data, look up customers, or read reports.
        </p>
        <div className="mt-6 grid gap-2 text-left w-full max-w-sm">
          {[
            'Show me top 5 customers by revenue',
            'What were our highest sales last quarter?',
            'List available files in the data directory',
            'Add a new customer: John Doe, john@example.com',
          ].map((s) => (
            <div key={s} className="bg-gray-800 rounded-lg px-3 py-2 text-xs text-gray-400 cursor-default">
              "{s}"
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isLoading && (
        <div className="flex justify-start mb-4">
          <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold mr-2 shrink-0">
            AI
          </div>
          <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
            <span className="text-xs text-gray-400">Thinking…</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
