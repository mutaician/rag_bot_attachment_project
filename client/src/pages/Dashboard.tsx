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
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    }
  }, [])

  // Load on mount + poll so status updates while worker runs
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
      setError(err instanceof Error ? err.message : 'Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  const isIndexing = documents.some(
    (d) => d.status === 'pending' || d.status === 'indexing',
  )

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-gray-100">Documents</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload files here — indexing runs automatically in the background.
          {isIndexing && (
            <span className="ml-1 text-blue-400">Refreshing status…</span>
          )}
        </p>
      </div>

      <UploadZone onUpload={handleUpload} disabled={uploading} />

      {uploading && (
        <p className="text-sm text-gray-400">Uploading…</p>
      )}

      {error && (
        <p className="rounded-md border border-red-900 bg-red-950 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-gray-500">
          Library
        </h2>
        <DocumentList
          documents={documents}
          onDelete={handleDelete}
          deletingId={deletingId}
        />
      </section>
    </div>
  )
}
