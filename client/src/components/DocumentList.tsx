import type { Document, DocumentStatus } from '../types/api'

const STATUS_LABEL: Record<DocumentStatus, string> = {
  pending: 'Queued',
  indexing: 'Indexing',
  ready: 'Ready',
  failed: 'Failed',
}

interface DocumentListProps {
  documents: Document[]
  onDelete: (id: string) => Promise<void>
  deletingId: string | null
}

export default function DocumentList({
  documents,
  onDelete,
  deletingId,
}: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <p className="text-sm text-muted">
        Nothing on file yet. Drop a document above to get started.
      </p>
    )
  }

  return (
    <ul className="divide-y divide-line border border-line bg-surface">
      {documents.map((doc) => (
        <li
          key={doc.id}
          className="flex items-start justify-between gap-4 px-4 py-3.5"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-ink">
              {doc.filename}
              <span className="ml-2 font-mono text-xs font-normal text-faint">
                v{doc.version}
              </span>
            </p>
            <p className="mt-0.5 font-mono text-[10px] text-faint">
              {new Date(doc.updated_at).toLocaleString()}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-3">
            <span
              className={[
                'font-mono text-[10px] uppercase tracking-wide',
                doc.status === 'ready' ? 'text-accent' : 'text-faint',
              ].join(' ')}
            >
              {STATUS_LABEL[doc.status]}
            </span>
            <button
              type="button"
              onClick={() => void onDelete(doc.id)}
              disabled={deletingId === doc.id}
              className="text-xs text-faint hover:text-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:opacity-50"
            >
              {deletingId === doc.id ? '…' : 'Remove'}
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}
