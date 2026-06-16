import type { Document, DocumentStatus } from '../types/api'

const STATUS_STYLES: Record<DocumentStatus, string> = {
  pending: 'bg-gray-700 text-gray-300',
  indexing: 'bg-blue-900 text-blue-200',
  ready: 'bg-green-900 text-green-200',
  failed: 'bg-red-900 text-red-200',
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
      <p className="text-sm text-gray-500">No documents yet. Upload one above.</p>
    )
  }

  return (
    <ul className="divide-y divide-gray-800 rounded-lg border border-gray-800">
      {documents.map((doc) => (
        <li
          key={doc.id}
          className="flex items-center justify-between gap-4 px-4 py-3"
        >
          <div className="min-w-0">
            <p className="truncate font-medium text-gray-100">
              {doc.filename}
              <span className="ml-2 text-sm font-normal text-gray-500">
                v{doc.version}
              </span>
            </p>
            <p className="text-xs text-gray-600">
              {new Date(doc.updated_at).toLocaleString()}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-3">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLES[doc.status]}`}
            >
              {doc.status}
            </span>
            <button
              type="button"
              onClick={() => void onDelete(doc.id)}
              disabled={deletingId === doc.id}
              className="text-sm text-gray-500 hover:text-red-400 disabled:opacity-50"
            >
              {deletingId === doc.id ? '…' : 'Remove'}
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}
