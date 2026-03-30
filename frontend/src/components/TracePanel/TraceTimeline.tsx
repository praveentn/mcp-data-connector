import { useEffect, useRef } from 'react'
import type { TraceEvent } from '../../types/trace'
import { TraceEventItem } from './TraceEventItem'

interface Props {
  traces: TraceEvent[]
}

export function TraceTimeline({ traces }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [traces])

  if (traces.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <div className="text-3xl mb-3">📡</div>
        <p className="text-sm text-gray-500">Waiting for agent activity…</p>
        <p className="text-xs text-gray-600 mt-1">
          Traces stream here in real time as the agent works.
        </p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2">
      {traces.map((t) => (
        <TraceEventItem key={t.id} event={t} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
