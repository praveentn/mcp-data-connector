import { useChatStore } from '../store/chatStore'
import { useTraceStore } from '../store/traceStore'

export function useChat() {
  const { sessionId, messages, isLoading, error, sendMessage, newSession: storeNewSession } =
    useChatStore()
  const clearTraces = useTraceStore((s) => s.clearTraces)

  const newSession = () => {
    storeNewSession()
    clearTraces()
  }

  return { sessionId, messages, isLoading, error, sendMessage, newSession }
}
