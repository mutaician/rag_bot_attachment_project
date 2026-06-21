/**
 * Thin fetch wrapper around the FastAPI backend.
 */

import type {
  AuthUser,
  ChatRequest,
  Citation,
  ConversationDetail,
  ConversationSummary,
  Document,
  LlmModeResponse,
  LoginRequest,
  SystemCapabilities,
  UploadResponse,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function apiFetch(input: string | URL, init?: RequestInit): Promise<Response> {
  return fetch(input, { ...init, credentials: 'include' })
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function parseError(res: Response, fallback: string): Promise<never> {
  const body = await res.json().catch(() => null)
  const detail = body?.detail
  const message =
    typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((d: { msg?: string }) => d.msg).join(', ')
        : `${fallback}: ${res.status}`
  throw new ApiError(res.status, message)
}

export async function getMe(): Promise<AuthUser> {
  const res = await apiFetch(`${API_BASE}/auth/me`)
  if (!res.ok) await parseError(res, 'GET /auth/me failed')
  return res.json()
}

export async function login(body: LoginRequest): Promise<AuthUser> {
  const res = await apiFetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) await parseError(res, 'Login failed')
  return res.json()
}

export async function logout(): Promise<void> {
  const res = await apiFetch(`${API_BASE}/auth/logout`, { method: 'POST' })
  if (!res.ok) await parseError(res, 'Logout failed')
}

export async function getDocuments(): Promise<Document[]> {
  const res = await apiFetch(`${API_BASE}/documents`)
  if (!res.ok) await parseError(res, 'GET /documents failed')
  return res.json()
}

export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const form = new FormData()
  for (const file of files) {
    form.append('files', file)
  }

  const res = await apiFetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: form,
  })

  if (!res.ok) await parseError(res, 'Upload failed')
  return res.json()
}

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

export async function* streamChat(
  body: ChatRequest,
): AsyncGenerator<ChatStreamEvent, void, unknown> {
  const res = await apiFetch(`${API_BASE}/chat`, {
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

export async function getConversations(): Promise<ConversationSummary[]> {
  const res = await apiFetch(`${API_BASE}/conversations`)
  if (!res.ok) await parseError(res, 'GET /conversations failed')
  return res.json()
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const res = await apiFetch(`${API_BASE}/conversations/${id}`)
  if (!res.ok) await parseError(res, `GET /conversations/${id} failed`)
  return res.json()
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await apiFetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' })
  if (!res.ok) await parseError(res, `DELETE /conversations/${id} failed`)
}

export async function deleteDocument(documentId: string, hard = false): Promise<void> {
  const url = new URL(`${API_BASE}/documents/${documentId}`)
  if (hard) url.searchParams.set('hard', 'true')

  const res = await apiFetch(url, { method: 'DELETE' })
  if (!res.ok) await parseError(res, `DELETE /documents/${documentId} failed`)
}

export async function getLlmMode(): Promise<LlmModeResponse> {
  const res = await apiFetch(`${API_BASE}/system/llm`)
  if (!res.ok) await parseError(res, 'GET /system/llm failed')
  return res.json()
}

export async function setLlmMode(mode: 'local' | 'cloud'): Promise<LlmModeResponse> {
  const res = await apiFetch(`${API_BASE}/system/llm`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  })
  if (!res.ok) await parseError(res, 'PUT /system/llm failed')
  return res.json()
}

export async function getCapabilities(): Promise<SystemCapabilities> {
  const res = await apiFetch(`${API_BASE}/system/capabilities`)
  if (!res.ok) await parseError(res, 'GET /system/capabilities failed')
  return res.json()
}
