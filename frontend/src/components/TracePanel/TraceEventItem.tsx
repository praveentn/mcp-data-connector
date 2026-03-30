import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { TraceEvent, TraceType } from '../../types/trace'
import { ToolCallCard } from './ToolCallCard'

const TRACE_CONFIG: Record<TraceType, { label: string; color: string; dot: string }> = {
  intent_detection: { label: 'Intent', color: 'text-purple-400', dot: 'bg-purple-400' },
  plan: { label: 'Plan', color: 'text-blue-400', dot: 'bg-blue-400' },
  tool_call: { label: 'Tool Call', color: 'text-orange-400', dot: 'bg-orange-400' },
  tool_result: { label: 'Tool Result', color: 'text-green-400', dot: 'bg-green-400' },
  delegation: { label: 'Delegation', color: 'text-yellow-400', dot: 'bg-yellow-400' },
  response: { label: 'Response', color: 'text-teal-400', dot: 'bg-teal-400' },
}

interface Props {
  event: TraceEvent
}

export function TraceEventItem({ event }: Props) {
  const [expanded, setExpanded] = useState(false)
  const config = TRACE_CONFIG[event.trace_type] ?? {
    label: event.trace_type,
    color: 'text-gray-400',
    dot: 'bg-gray-400',
  }

  const isToolEvent = event.trace_type === 'tool_call' || event.trace_type === 'tool_result'

  const summary = getSummary(event)

  return (
    <div
      className="border border-gray-800 rounded-lg bg-gray-900 hover:border-gray-700 transition-colors"
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 text-left"
      >
        <div className={`w-2 h-2 rounded-full shrink-0 ${config.dot}`} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-semibold ${config.color}`}>{config.label}</span>
            {event.tool_name && (
              <span className="text-xs text-gray-400 font-mono bg-gray-800 px-1.5 py-0.5 rounded">
                {event.tool_name}
              </span>
            )}
            <span
              className={`ml-auto text-xs px-1.5 py-0.5 rounded font-medium ${
                event.status === 'success'
                  ? 'text-green-400 bg-green-400/10'
                  : event.status === 'error'
                  ? 'text-red-400 bg-red-400/10'
                  : 'text-yellow-400 bg-yellow-400/10'
              }`}
            >
              {event.status}
            </span>
          </div>
          {summary && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{summary}</p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {event.duration_ms != null && (
            <span className="text-xs text-gray-600">{event.duration_ms}ms</span>
          )}
          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 border-t border-gray-800 pt-2">
          {isToolEvent ? (
            <ToolCallCard event={event} />
          ) : (
            <pre className="text-xs font-mono text-gray-400 bg-gray-950 rounded p-2 overflow-x-auto whitespace-pre-wrap max-h-48">
              {JSON.stringify(event.payload, null, 2)}
            </pre>
          )}
          <p className="text-xs text-gray-600 mt-2">
            {new Date(event.created_at).toLocaleTimeString()}
          </p>
        </div>
      )}
    </div>
  )
}

function getSummary(event: TraceEvent): string {
  const p = event.payload
  switch (event.trace_type) {
    case 'intent_detection':
      return `Detected: ${p.detected_intent}`
    case 'plan':
      return Array.isArray(p.plan) ? `${(p.plan as unknown[]).length} step(s) planned` : ''
    case 'tool_call':
      return `Calling ${event.tool_name}`
    case 'tool_result':
      return event.status === 'error' ? String(p.error) : 'Result received'
    case 'delegation':
      return `→ ${p.selected_agent}`
    case 'response':
      return `${p.response_length} chars composed`
    default:
      return ''
  }
}
