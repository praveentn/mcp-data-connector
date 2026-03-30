import { create } from 'zustand'
import type { TraceEvent, TraceType } from '../types/trace'

interface TraceStore {
  traces: TraceEvent[]
  isConnected: boolean
  filter: TraceType | 'all'

  addTrace: (event: TraceEvent) => void
  clearTraces: () => void
  setConnected: (connected: boolean) => void
  setFilter: (f: TraceType | 'all') => void

  filteredTraces: () => TraceEvent[]
}

export const useTraceStore = create<TraceStore>((set, get) => ({
  traces: [],
  isConnected: false,
  filter: 'all',

  addTrace: (event) =>
    set((s) => ({ traces: [...s.traces, event] })),

  clearTraces: () => set({ traces: [] }),

  setConnected: (connected) => set({ isConnected: connected }),

  setFilter: (f) => set({ filter: f }),

  filteredTraces: () => {
    const { traces, filter } = get()
    return filter === 'all' ? traces : traces.filter((t) => t.trace_type === filter)
  },
}))
