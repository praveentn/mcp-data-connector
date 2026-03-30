import { useEffect } from 'react'
import { useChatStore } from './store/chatStore'
import { useWebSocket } from './hooks/useWebSocket'
import { Header } from './components/Layout/Header'
import { SplitLayout } from './components/Layout/SplitLayout'
import { ChatPanel } from './components/ChatPanel/ChatPanel'
import { RightPanel } from './components/RightPanel/RightPanel'

export default function App() {
  const sessionId = useChatStore((s) => s.sessionId)
  const loadHistory = useChatStore((s) => s.loadHistory)

  // Connect WebSocket immediately — sessionId exists before first message
  useWebSocket(sessionId)

  // Load conversation history on mount
  useEffect(() => {
    loadHistory()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header />
      <SplitLayout
        left={<ChatPanel />}
        right={<RightPanel />}
      />
    </div>
  )
}
