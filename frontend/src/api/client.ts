import axios from 'axios'
import type { Message, ChatResponse } from '../types/chat'
import type { TraceEvent } from '../types/trace'

const http = axios.create({
  baseURL: '/api',
  timeout: 60_000,
})

export async function sendMessage(
  sessionId: string | null,
  message: string,
): Promise<ChatResponse> {
  const { data } = await http.post<ChatResponse>('/chat/send', {
    session_id: sessionId,
    message,
  })
  return data
}

export async function getChatHistory(sessionId: string): Promise<Message[]> {
  const { data } = await http.get<Message[]>(`/chat/history/${sessionId}`)
  return data
}

export async function getTraces(sessionId: string): Promise<TraceEvent[]> {
  const { data } = await http.get<TraceEvent[]>(`/traces/${sessionId}`)
  return data
}

export async function getAgents() {
  const { data } = await http.get('/agents')
  return data
}

export async function getTools() {
  const { data } = await http.get('/tools')
  return data
}

export async function discoverMcpTools() {
  const { data } = await http.get('/tools/mcp/discover')
  return data
}
