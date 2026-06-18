/**
 * Thin fetch wrapper around the FastAPI backend.
 * All HTTP calls go through here so the base URL lives in one place.
 */

import type {
  ChatRequest,
  Citation,
  ConversationDetail,
  ConversationSummary,
  Document,
  UploadResponse,
} from '../types/api'

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

/** SSE events from POST /chat */
export type ChatStreamEvent =
  | { type: 'token'; content: string }
  | { type: 'tool'; name: string; status: string; query?: string }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'done'; conversation_id: string }
  | { type: 'error'; message: string }

function parseSseBlock(block: string): ChatStreamEvent | null {
  let eventType = 'message'
  let dataLine = ''
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) eventType = line.slice(6).trim()
    if (line.startsWith('data:')) dataLine = line.slice(5).trim()
  }
  if (!dataLine) return null
  const data = JSON.parse(dataLine) as Record<string, unknown>

  switch (eventType) {
    case 'token':
      return { type: 'token', content: String(data.content ?? '') }
    case 'tool':
      return {
        type: 'tool',
        name: String(data.name ?? ''),
        status: String(data.status ?? ''),
        query: data.query != null ? String(data.query) : undefined,
      }
    case 'citations':
      return { type: 'citations', citations: (data.citations as Citation[]) ?? [] }
    case 'done':
      return { type: 'done', conversation_id: String(data.conversation_id ?? '') }
    case 'error':
      return { type: 'error', message: String(data.message ?? 'Unknown error') }
    default:
      return null
  }
}

/** POST /chat — stream SSE events (token, citations, done, error). */
export async function* streamChat(
  body: ChatRequest,
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`POST /chat failed: ${res.status} ${detail}`)
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''

    for (const block of blocks) {
      if (!block.trim()) continue
      const event = parseSseBlock(block)
      if (event) yield event
    }
  }

  if (buffer.trim()) {
    const event = parseSseBlock(buffer)
    if (event) yield event
  }
}

/** GET /conversations — list chat threads. */
export async function getConversations(): Promise<ConversationSummary[]> {
  const res = await fetch(`${API_BASE}/conversations`)
  if (!res.ok) throw new Error(`GET /conversations failed: ${res.status}`)
  return res.json()
}

/** GET /conversations/{id} — full history. */
export async function getConversation(id: string): Promise<ConversationDetail> {
  const res = await fetch(`${API_BASE}/conversations/${id}`)
  if (!res.ok) throw new Error(`GET /conversations/${id} failed: ${res.status}`)
  return res.json()
}

/** DELETE /conversations/{id} */
export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`DELETE /conversations/${id} failed: ${res.status}`)
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
