import { Activity, Trash2 } from 'lucide-react'
import { useTraces } from '../../hooks/useTraces'
import { TraceTimeline } from './TraceTimeline'
import type { TraceType } from '../../types/trace'

const FILTER_OPTIONS: { label: string; value: TraceType | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Intent', value: 'intent_detection' },
  { label: 'Plan', value: 'plan' },
  { label: 'Tools', value: 'tool_call' },
  { label: 'Results', value: 'tool_result' },
  { label: 'Delegation', value: 'delegation' },
  { label: 'Response', value: 'response' },
]

export function TracePanel() {
  const { filteredTraces, traces, isConnected, filter, setFilter, clearTraces } = useTraces()

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
        <Activity className="w-4 h-4 text-green-400" />
        <span className="text-sm font-medium text-gray-300">MCP Trace Stream</span>
        <span className="ml-1 text-xs text-gray-600">({traces.length} events)</span>

        <div className="ml-auto flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}`} />
          <button
            onClick={clearTraces}
            className="p-1.5 text-gray-600 hover:text-gray-400 hover:bg-gray-800 rounded transition-colors"
            title="Clear traces"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex gap-1 px-4 py-2 border-b border-gray-800 bg-gray-900/50 overflow-x-auto scrollbar-hidden shrink-0">
        {FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setFilter(opt.value)}
            className={`
              shrink-0 px-2.5 py-1 text-xs rounded-full transition-colors
              ${filter === opt.value
                ? 'bg-blue-600 text-white'
                : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800'
              }
            `}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <TraceTimeline traces={filteredTraces} />
    </div>
  )
}
