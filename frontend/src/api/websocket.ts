import type { TraceEvent, TraceStreamMessage } from '../types/trace'

type MessageHandler = (event: TraceEvent) => void
type StatusHandler = (connected: boolean) => void

export class TraceWebSocket {
  private ws: WebSocket | null = null
  private sessionId: string
  private onMessage: MessageHandler
  private onStatus: StatusHandler
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectDelay = 1000
  private shouldReconnect = true

  constructor(sessionId: string, onMessage: MessageHandler, onStatus: StatusHandler) {
    this.sessionId = sessionId
    this.onMessage = onMessage
    this.onStatus = onStatus
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/traces/${this.sessionId}`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectDelay = 1000
      this.onStatus(true)
      // Start keep-alive ping every 20s
      this._startPing()
    }

    this.ws.onmessage = (event) => {
      try {
        const msg: TraceStreamMessage = JSON.parse(event.data)
        if (msg.event === 'trace' && msg.data) {
          this.onMessage(msg.data)
        }
        // ignore 'pong' messages
      } catch {
        // ignore parse errors
      }
    }

    this.ws.onclose = () => {
      this._stopPing()
      this.onStatus(false)
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => {
          this.reconnectDelay = Math.min(this.reconnectDelay * 2, 10_000)
          this.connect()
        }, this.reconnectDelay)
      }
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  disconnect() {
    this.shouldReconnect = false
    this._stopPing()
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
    this.ws = null
    this.onStatus(false)
  }

  private _pingTimer: ReturnType<typeof setInterval> | null = null

  private _startPing() {
    this._pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send('ping')
      }
    }, 20_000)
  }

  private _stopPing() {
    if (this._pingTimer) {
      clearInterval(this._pingTimer)
      this._pingTimer = null
    }
  }
}
