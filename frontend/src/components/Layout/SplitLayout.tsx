import type { ReactNode } from 'react'

interface Props {
  left: ReactNode
  right: ReactNode
}

export function SplitLayout({ left, right }: Props) {
  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left — Chat */}
      <div className="flex flex-col w-1/2 border-r border-gray-800 overflow-hidden">
        {left}
      </div>

      {/* Right — Trace Panel */}
      <div className="flex flex-col w-1/2 overflow-hidden">
        {right}
      </div>
    </div>
  )
}
