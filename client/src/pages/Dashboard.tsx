import { useCallback, useEffect, useState } from 'react'
import {
  deleteDocument,
  getDocuments,
  uploadDocuments,
} from '../api/client'
import type { Document } from '../types/api'
import DocumentList from '../components/DocumentList'
import UploadZone from '../components/UploadZone'

const POLL_MS = 3000

export default function Dashboard() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const data = await getDocuments()
      setDocuments(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load library')
    }
  }, [])

  useEffect(() => {
    void refresh()
    const id = setInterval(() => void refresh(), POLL_MS)
    return () => clearInterval(id)
  }, [refresh])

  async function handleUpload(files: File[]) {
    setUploading(true)
    setError(null)
    try {
      await uploadDocuments(files)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id)
    setError(null)
    try {
      await deleteDocument(id)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not remove file')
    } finally {
      setDeletingId(null)
    }
  }

  const isIndexing = documents.some(
    (d) => d.status === 'pending' || d.status === 'indexing',
  )

  return (
    <div className="px-5 py-8 md:px-10 md:py-10">
      <header className="max-w-2xl">
        <h1 className="font-display text-3xl font-semibold tracking-tight">
          Library
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Add PDFs and text files here. Each upload is indexed for search in Ask.
          {isIndexing && (
            <span className="ml-2 font-mono text-xs text-accent">
              Indexing in progress
            </span>
          )}
        </p>
      </header>

      <div className="mt-8 max-w-2xl space-y-8">
        <UploadZone onUpload={handleUpload} disabled={uploading} />

        {uploading && (
          <p className="font-mono text-xs text-faint">Uploading files…</p>
        )}

        {error && (
          <p
            role="alert"
            className="border border-accent/30 bg-accent-soft px-3 py-2 text-sm text-accent"
          >
            {error}
          </p>
        )}

        <section>
          <h2 className="mb-3 font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-faint">
            On file
          </h2>
          <DocumentList
            documents={documents}
            onDelete={handleDelete}
            deletingId={deletingId}
          />
        </section>
      </div>
    </div>
  )
}
