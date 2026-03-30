import { useEffect, useState } from 'react'
import { Plug, RefreshCw, ChevronDown, ChevronRight, CheckCircle, XCircle } from 'lucide-react'
import { getTools, discoverMcpTools } from '../../api/client'

interface Tool {
  id: string
  name: string
  description: string | null
  input_schema: Record<string, unknown>
  permission_level: string
}

interface McpTool {
  name: string
  description: string
  input_schema: Record<string, unknown>
}

const PERM_COLOR: Record<string, string> = {
  read: 'text-green-400 bg-green-400/10',
  write: 'text-yellow-400 bg-yellow-400/10',
  admin: 'text-red-400 bg-red-400/10',
}

export function ToolsPanel() {
  const [tools, setTools] = useState<Tool[]>([])
  const [mcpTools, setMcpTools] = useState<McpTool[]>([])
  const [mcpOnline, setMcpOnline] = useState<boolean | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [reg, mcp] = await Promise.allSettled([getTools(), discoverMcpTools()])
      if (reg.status === 'fulfilled') setTools(reg.value)
      if (mcp.status === 'fulfilled') {
        setMcpTools(mcp.value.tools ?? [])
        setMcpOnline(true)
      } else {
        setMcpOnline(false)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* MCP Server status bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-900 shrink-0">
        <div className="flex items-center gap-2">
          {mcpOnline === true && <CheckCircle className="w-3.5 h-3.5 text-green-400" />}
          {mcpOnline === false && <XCircle className="w-3.5 h-3.5 text-red-400" />}
          {mcpOnline === null && <div className="w-3.5 h-3.5 rounded-full bg-gray-600 animate-pulse" />}
          <span className="text-xs text-gray-400">
            MCP Server&nbsp;
            <span className="font-mono text-gray-500">:7792</span>
            &nbsp;—&nbsp;
            <span className={mcpOnline ? 'text-green-400' : 'text-red-400'}>
              {mcpOnline === null ? 'checking...' : mcpOnline ? 'online' : 'offline'}
            </span>
          </span>
        </div>
        <button onClick={load} className="p-1.5 text-gray-600 hover:text-gray-400 hover:bg-gray-800 rounded transition-colors">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Live MCP tools */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Plug className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Live MCP Tools ({mcpTools.length})
            </span>
          </div>
          <div className="space-y-1.5">
            {loading ? (
              <p className="text-xs text-gray-600 py-2">Loading...</p>
            ) : mcpTools.length === 0 ? (
              <p className="text-xs text-gray-600 py-2">
                {mcpOnline ? 'No tools found' : 'MCP server offline — run ./start.sh'}
              </p>
            ) : mcpTools.map(tool => (
              <div key={tool.name} className="border border-gray-800 rounded-lg bg-gray-900">
                <button
                  onClick={() => setExpanded(expanded === tool.name ? null : tool.name)}
                  className="w-full flex items-center gap-3 p-2.5 text-left"
                >
                  <span className="text-xs font-mono text-blue-300 font-semibold flex-1">{tool.name}</span>
                  {expanded === tool.name
                    ? <ChevronDown className="w-3 h-3 text-gray-600" />
                    : <ChevronRight className="w-3 h-3 text-gray-600" />
                  }
                </button>
                {expanded === tool.name && (
                  <div className="px-3 pb-3 border-t border-gray-800 pt-2 space-y-2">
                    <p className="text-xs text-gray-400">{tool.description}</p>
                    {Object.keys(tool.input_schema?.properties ?? {}).length > 0 && (
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Parameters:</p>
                        <pre className="text-xs font-mono text-gray-400 bg-gray-950 rounded p-2 overflow-x-auto">
                          {JSON.stringify(tool.input_schema?.properties, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Registry tools */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Tool Registry ({tools.length})
            </span>
          </div>
          <div className="space-y-1.5">
            {tools.map(tool => (
              <div key={tool.id} className="flex items-center gap-3 p-2.5 border border-gray-800 rounded-lg bg-gray-900">
                <span className="text-xs font-mono text-gray-300 flex-1">{tool.name}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${PERM_COLOR[tool.permission_level] ?? 'text-gray-400 bg-gray-800'}`}>
                  {tool.permission_level}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
