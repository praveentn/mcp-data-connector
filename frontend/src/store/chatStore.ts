import { create } from 'zustand'
import type { Message } from '../types/chat'
import { sendMessage as apiSend, getChatHistory } from '../api/client'

const STORAGE_KEY = 'mcp_session_id'

function loadOrCreateSessionId(): string {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) return saved
  const fresh = crypto.randomUUID()
  localStorage.setItem(STORAGE_KEY, fresh)
  return fresh
}

interface ChatStore {
  sessionId: string
  messages: Message[]
  isLoading: boolean
  error: string | null
  historyLoaded: boolean

  sendMessage: (text: string) => Promise<void>
  loadHistory: () => Promise<void>
  newSession: () => void
}

export const useChatStore = create<ChatStore>((set, get) => ({
  sessionId: loadOrCreateSessionId(),
  messages: [],
  isLoading: false,
  error: null,
  historyLoaded: false,

  loadHistory: async () => {
    if (get().historyLoaded) return
    try {
      const msgs = await getChatHistory(get().sessionId)
      set({ messages: msgs, historyLoaded: true })
    } catch {
      set({ historyLoaded: true })
    }
  },

  sendMessage: async (text) => {
    set({ isLoading: true, error: null })

    // Optimistic user bubble
    const optimistic: Message = {
      id: `opt-${Date.now()}`,
      session_id: get().sessionId,
      role: 'user',
      content: text,
      metadata: {},
      created_at: new Date().toISOString(),
    }
    set((s) => ({ messages: [...s.messages, optimistic] }))

    try {
      const res = await apiSend(get().sessionId, text)

      const assistantMsg: Message = {
        id: `resp-${Date.now()}`,
        session_id: get().sessionId,
        role: 'assistant',
        content: res.message,
        metadata: res.metadata,
        created_at: new Date().toISOString(),
      }
      set((s) => ({ messages: [...s.messages, assistantMsg], isLoading: false }))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Request failed'
      set({ isLoading: false, error: msg })
    }
  },

  newSession: () => {
    const id = crypto.randomUUID()
    localStorage.setItem(STORAGE_KEY, id)
    set({ sessionId: id, messages: [], error: null, historyLoaded: false })
  },
}))
