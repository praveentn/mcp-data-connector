import type { TraceEvent } from '../../types/trace'

interface Props {
  event: TraceEvent
}

export function ToolCallCard({ event }: Props) {
  const payload = event.payload

  return (
    <div className="mt-2 space-y-2 text-xs font-mono">
      {payload.args !== undefined && (
        <div>
          <p className="text-gray-500 mb-1">Arguments:</p>
          <pre className="bg-gray-900 rounded p-2 text-gray-300 overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(payload.args, null, 2)}
          </pre>
        </div>
      )}
      {payload.result !== undefined && (
        <div>
          <p className="text-gray-500 mb-1">Result:</p>
          <pre className="bg-gray-900 rounded p-2 text-green-300 overflow-x-auto whitespace-pre-wrap max-h-48">
            {typeof payload.result === 'string'
              ? payload.result
              : JSON.stringify(payload.result, null, 2)}
          </pre>
        </div>
      )}
      {payload.error !== undefined && (
        <div>
          <p className="text-gray-500 mb-1">Error:</p>
          <pre className="bg-gray-900 rounded p-2 text-red-400 overflow-x-auto whitespace-pre-wrap">
            {String(payload.error)}
          </pre>
        </div>
      )}
    </div>
  )
}
