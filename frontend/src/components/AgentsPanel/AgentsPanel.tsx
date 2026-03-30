import { useEffect, useState } from 'react'
import { Bot, Plus, Trash2, ChevronDown, ChevronRight } from 'lucide-react'
import { getAgents } from '../../api/client'
import axios from 'axios'

interface Agent {
  id: string
  name: string
  description: string | null
  agent_type: string
  capabilities: string[]
  config: Record<string, unknown>
  is_active: boolean
  created_at: string
}

const TYPE_COLOR: Record<string, string> = {
  main: 'text-blue-400 bg-blue-400/10',
  sub: 'text-green-400 bg-green-400/10',
}

export function AgentsPanel() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', capabilities: '' })
  const [creating, setCreating] = useState(false)

  const load = async () => {
    try {
      setLoading(true)
      const data = await getAgents()
      setAgents(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const createAgent = async () => {
    if (!form.name.trim()) return
    setCreating(true)
    try {
      await axios.post('/api/agents', {
        name: form.name.trim(),
        description: form.description.trim() || null,
        agent_type: 'sub',
        capabilities: form.capabilities.split(',').map(s => s.trim()).filter(Boolean),
        config: {},
      })
      setForm({ name: '', description: '', capabilities: '' })
      setShowForm(false)
      await load()
    } finally {
      setCreating(false)
    }
  }

  const deleteAgent = async (id: string) => {
    await axios.delete(`/api/agents/${id}`)
    await load()
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
        <span className="text-sm text-gray-400">
          {agents.length} agent{agents.length !== 1 ? 's' : ''} active
        </span>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-blue-400
                     bg-blue-400/10 hover:bg-blue-400/20 rounded-lg transition-colors"
        >
          <Plus className="w-3.5 h-3.5" /> New Agent
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="p-4 border-b border-gray-800 bg-gray-900/50 shrink-0 space-y-2">
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100
                       placeholder-gray-500 outline-none focus:border-blue-500"
            placeholder="Agent name *"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          />
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100
                       placeholder-gray-500 outline-none focus:border-blue-500"
            placeholder="Description"
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          />
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100
                       placeholder-gray-500 outline-none focus:border-blue-500"
            placeholder="Capabilities (comma-separated, e.g. query_sales_db, get_customers)"
            value={form.capabilities}
            onChange={e => setForm(f => ({ ...f, capabilities: e.target.value }))}
          />
          <div className="flex gap-2">
            <button
              onClick={createAgent}
              disabled={creating || !form.name.trim()}
              className="flex-1 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500
                         disabled:opacity-40 rounded-lg transition-colors"
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200 bg-gray-800 rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Agent list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {loading ? (
          <p className="text-center text-xs text-gray-500 py-8">Loading...</p>
        ) : agents.length === 0 ? (
          <p className="text-center text-xs text-gray-500 py-8">No agents yet</p>
        ) : (
          agents.map(agent => (
            <div key={agent.id} className="border border-gray-800 rounded-lg bg-gray-900 hover:border-gray-700 transition-colors">
              <button
                onClick={() => setExpanded(expanded === agent.id ? null : agent.id)}
                className="w-full flex items-center gap-3 p-3 text-left"
              >
                <Bot className="w-4 h-4 text-gray-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-200 truncate">{agent.name}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${TYPE_COLOR[agent.agent_type] ?? 'text-gray-400 bg-gray-700'}`}>
                      {agent.agent_type}
                    </span>
                  </div>
                  {agent.description && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate">{agent.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {agent.agent_type !== 'main' && (
                    <button
                      onClick={e => { e.stopPropagation(); deleteAgent(agent.id) }}
                      className="p-1 text-gray-600 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {expanded === agent.id
                    ? <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
                    : <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
                  }
                </div>
              </button>

              {expanded === agent.id && (
                <div className="px-4 pb-3 border-t border-gray-800 pt-2 space-y-2">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Capabilities</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.capabilities.length === 0
                        ? <span className="text-xs text-gray-600">None assigned</span>
                        : agent.capabilities.map(cap => (
                          <span key={cap} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded-full font-mono">
                            {cap}
                          </span>
                        ))
                      }
                    </div>
                  </div>
                  {agent.config.system_prompt && (
                    <div>
                      <p className="text-xs text-gray-500 mb-1">System Prompt</p>
                      <p className="text-xs text-gray-400 bg-gray-950 rounded p-2">
                        {String(agent.config.system_prompt)}
                      </p>
                    </div>
                  )}
                  <p className="text-xs text-gray-600">
                    Created {new Date(agent.created_at).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
