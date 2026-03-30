import ReactMarkdown from 'react-markdown'
import type { Message } from '../../types/chat'

interface Props {
  message: Message
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold mr-2 shrink-0 mt-1">
          AI
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`
            rounded-2xl px-4 py-3 text-sm leading-relaxed
            ${isUser
              ? 'bg-blue-600 text-white rounded-tr-sm'
              : 'bg-gray-800 text-gray-100 rounded-tl-sm'
            }
          `}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm prose-invert max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>
        <p className="text-xs text-gray-600 mt-1 px-1">
          {new Date(message.created_at).toLocaleTimeString()}
        </p>
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold ml-2 shrink-0 mt-1">
          U
        </div>
      )}
    </div>
  )
}
