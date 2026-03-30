export type TraceType =
  | 'intent_detection'
  | 'plan'
  | 'tool_call'
  | 'tool_result'
  | 'delegation'
  | 'response'

export interface TraceEvent {
  id: string
  session_id: string
  agent_id: string | null
  trace_type: TraceType
  payload: Record<string, unknown>
  tool_name: string | null
  duration_ms: number | null
  status: 'running' | 'success' | 'error'
  created_at: string
}

export interface TraceStreamMessage {
  event: 'trace'
  data: TraceEvent
}
