import type { Citation } from '../types/api'
import CitationCard from './CitationCard'

export interface ChatMessageData {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  streaming?: boolean
}

interface ChatMessageProps {
  message: ChatMessageData
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[90%] border border-line bg-surface px-4 py-3 text-sm leading-relaxed text-ink">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <article className="max-w-none">
      <p className="whitespace-pre-wrap text-sm leading-[1.65] text-ink">
        {message.content}
        {message.streaming && (
          <span
            className="ml-0.5 inline-block h-[1em] w-0.5 animate-pulse bg-accent align-middle"
            aria-hidden
          />
        )}
      </p>

      {message.citations && message.citations.length > 0 && (
        <footer className="mt-5 space-y-3 border-t border-line pt-4">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-faint">
            Referenced passages
          </p>
          {message.citations.map((c, i) => (
            <CitationCard key={`${c.document_id}-${i}`} citation={c} index={i} />
          ))}
        </footer>
      )}
    </article>
  )
}
