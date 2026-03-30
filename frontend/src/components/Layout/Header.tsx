import { Database, Wifi, WifiOff, Plus } from 'lucide-react'
import { useChat } from '../../hooks/useChat'
import { useTraces } from '../../hooks/useTraces'

export function Header() {
  const { sessionId, newSession } = useChat()
  const { isConnected } = useTraces()

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-gray-900 border-b border-gray-800 shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-blue-400">
          <Database className="w-5 h-5" />
          <span className="font-bold text-white text-lg tracking-tight">MCP Data Connector</span>
        </div>
        <span className="hidden sm:inline text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">
          FastMCP + LangGraph
        </span>
      </div>

      <div className="flex items-center gap-3">
        {sessionId && (
          <span className="hidden md:inline text-xs text-gray-500 font-mono">
            {sessionId.slice(0, 8)}…
          </span>
        )}

        <div className="flex items-center gap-1.5 text-xs">
          {isConnected ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-green-400" />
              <span className="text-green-400">Live</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-gray-500">Connecting…</span>
            </>
          )}
        </div>

        <button
          onClick={newSession}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-300
                     bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New Session
        </button>
      </div>
    </header>
  )
}
