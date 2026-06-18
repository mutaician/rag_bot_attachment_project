import type { ConversationSummary } from '../types/api'

function formatWhen(iso: string): string {
  const date = new Date(iso)
  const now = new Date()
  const sameDay =
    date.getDate() === now.getDate() &&
    date.getMonth() === now.getMonth() &&
    date.getFullYear() === now.getFullYear()
  if (sameDay) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

interface ConversationSidebarProps {
  conversations: ConversationSummary[]
  activeId: string | null
  loading: boolean
  onSelect: (id: string) => void
  onNew: () => void
  onDelete: (id: string) => void
}

export default function ConversationSidebar({
  conversations,
  activeId,
  loading,
  onSelect,
  onNew,
  onDelete,
}: ConversationSidebarProps) {
  return (
    <aside className="flex w-full shrink-0 flex-col border-line bg-surface md:w-56 md:border-r lg:w-64">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <h2 className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-faint">
          Threads
        </h2>
        <button
          type="button"
          onClick={onNew}
          className="font-mono text-[11px] font-medium uppercase tracking-wide text-accent hover:text-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          New
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {loading && conversations.length === 0 && (
          <p className="px-4 py-6 font-mono text-xs text-faint">Loading…</p>
        )}

        {!loading && conversations.length === 0 && (
          <p className="px-4 py-6 text-sm leading-relaxed text-muted">
            No threads yet. Ask something about your library.
          </p>
        )}

        <ul className="space-y-0.5 px-2">
          {conversations.map((c) => {
            const active = c.id === activeId
            return (
              <li key={c.id} className="group relative">
                <button
                  type="button"
                  onClick={() => onSelect(c.id)}
                  className={[
                    'w-full rounded-md px-3 py-2.5 text-left transition-colors',
                    'focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent',
                    active
                      ? 'bg-accent-soft text-ink'
                      : 'text-muted hover:bg-paper-deep hover:text-ink',
                  ].join(' ')}
                >
                  <span className="line-clamp-2 text-sm leading-snug">{c.title}</span>
                  <span className="mt-1 block font-mono text-[10px] text-faint">
                    {formatWhen(c.updated_at)}
                  </span>
                </button>
                <button
                  type="button"
                  aria-label="Delete thread"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(c.id)
                  }}
                  className="absolute right-2 top-2 rounded px-1.5 py-0.5 font-mono text-[10px] text-faint opacity-0 transition-opacity hover:text-accent group-hover:opacity-100 focus-visible:opacity-100 focus-visible:outline-2 focus-visible:outline-accent"
                >
                  ×
                </button>
              </li>
            )
          })}
        </ul>
      </div>
    </aside>
  )
}
