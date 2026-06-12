/**
 * Thin fetch wrapper around the FastAPI backend.
 * All HTTP calls go through here so the base URL lives in one place.
 */

import type { ChatRequest, ChatResponse, Document } from '../types/api'

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
