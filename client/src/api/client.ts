/**
 * Thin fetch wrapper around the FastAPI backend.
 * All HTTP calls go through here so the base URL lives in one place.
 */

import type { ChatRequest, ChatResponse, Document, UploadResponse } from '../types/api'

// Vite exposes env vars prefixed with VITE_ — see client/.env
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/** GET /documents — list all documents and their indexing status. */
export async function getDocuments(): Promise<Document[]> {
  const res = await fetch(`${API_BASE}/documents`)
  if (!res.ok) {
    throw new Error(`GET /documents failed: ${res.status}`)
  }
  return res.json()
}

/** POST /documents/upload — multipart upload (field name must be `files`). */
export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const form = new FormData()
  for (const file of files) {
    form.append('files', file)
  }

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).join(', ')
          : `Upload failed: ${res.status}`
    throw new Error(message)
  }

  return res.json()
}

/** POST /chat — send a message and get a reply with citations (mock in M1). */
export async function postChat(body: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`POST /chat failed: ${res.status}`)
  }
  return res.json()
}

/** DELETE /documents/{id} — soft delete by default; pass hard=true to purge. */
export async function deleteDocument(
  documentId: string,
  hard = false,
): Promise<void> {
  const url = new URL(`${API_BASE}/documents/${documentId}`)
  if (hard) url.searchParams.set('hard', 'true')

  const res = await fetch(url, { method: 'DELETE' })
  if (!res.ok) {
    throw new Error(`DELETE /documents/${documentId} failed: ${res.status}`)
  }
}
