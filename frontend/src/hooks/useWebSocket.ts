import { useEffect, useRef } from 'react'
import { TraceWebSocket } from '../api/websocket'
import { useTraceStore } from '../store/traceStore'

export function useWebSocket(sessionId: string | null) {
  const addTrace = useTraceStore((s) => s.addTrace)
  const setConnected = useTraceStore((s) => s.setConnected)
  const wsRef = useRef<TraceWebSocket | null>(null)

  useEffect(() => {
    if (!sessionId) return

    // Cleanup previous connection
    wsRef.current?.disconnect()

    const ws = new TraceWebSocket(sessionId, addTrace, setConnected)
    ws.connect()
    wsRef.current = ws

    return () => {
      ws.disconnect()
      wsRef.current = null
    }
  }, [sessionId, addTrace, setConnected])

  return { isConnected: useTraceStore((s) => s.isConnected) }
}
