import { useState } from 'react'
import { Activity, Bot, Plug } from 'lucide-react'
import { TracePanel } from '../TracePanel/TracePanel'
import { AgentsPanel } from '../AgentsPanel/AgentsPanel'
import { ToolsPanel } from '../ToolsPanel/ToolsPanel'
import { useTraceStore } from '../../store/traceStore'

type Tab = 'traces' | 'agents' | 'tools'

export function RightPanel() {
  const [tab, setTab] = useState<Tab>('traces')
  const traceCount = useTraceStore(s => s.traces.length)

  const tabs: { id: Tab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'traces', label: 'Traces', icon: <Activity className="w-3.5 h-3.5" />, badge: traceCount || undefined },
    { id: 'agents', label: 'Agents', icon: <Bot className="w-3.5 h-3.5" /> },
    { id: 'tools', label: 'Connectors', icon: <Plug className="w-3.5 h-3.5" /> },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex border-b border-gray-800 bg-gray-900 shrink-0">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`
              flex items-center gap-1.5 px-4 py-3 text-xs font-medium transition-colors relative
              ${tab === t.id
                ? 'text-blue-400 border-b-2 border-blue-500'
                : 'text-gray-500 hover:text-gray-300'
              }
            `}
          >
            {t.icon}
            {t.label}
            {t.badge != null && t.badge > 0 && (
              <span className="ml-0.5 bg-blue-600 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center leading-none">
                {t.badge > 99 ? '99+' : t.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {tab === 'traces' && <TracePanel />}
        {tab === 'agents' && <AgentsPanel />}
        {tab === 'tools' && <ToolsPanel />}
      </div>
    </div>
  )
}
