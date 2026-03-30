export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  metadata: Record<string, unknown>
  created_at: string
}

export interface ChatResponse {
  session_id: string
  message: string
  metadata: Record<string, unknown>
}
