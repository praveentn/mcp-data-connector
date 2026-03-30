import { useState, useRef, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

interface Props {
  onSend: (text: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const onInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div className="p-4 border-t border-gray-800 bg-gray-900">
      <div className="flex items-end gap-3 bg-gray-800 rounded-xl p-3 border border-gray-700 focus-within:border-blue-500 transition-colors">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          onInput={onInput}
          placeholder="Ask me anything about your data…"
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-sm text-gray-100 placeholder-gray-500
                     resize-none outline-none leading-relaxed max-h-40"
        />
        <button
          onClick={submit}
          disabled={disabled || !text.trim()}
          className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40
                     disabled:cursor-not-allowed transition-colors shrink-0"
        >
          <Send className="w-4 h-4 text-white" />
        </button>
      </div>
      <p className="text-xs text-gray-600 mt-1.5 px-1">
        Press Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
