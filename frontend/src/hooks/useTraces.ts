import { useTraceStore } from '../store/traceStore'

export function useTraces() {
  const { traces, isConnected, filter, setFilter, clearTraces, filteredTraces } =
    useTraceStore()

  return {
    traces,
    filteredTraces: filteredTraces(),
    isConnected,
    filter,
    setFilter,
    clearTraces,
  }
}
