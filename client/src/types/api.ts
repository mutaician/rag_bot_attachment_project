/**
 * API contract — TypeScript mirror of server/app/schemas.py
 *
 * Keep these types in sync with the Python Pydantic models.
 * fetch() returns plain JSON strings; these types document the expected shape.
 */

/** Indexing lifecycle for an uploaded document. */
export type DocumentStatus = "pending" | "indexing" | "ready" | "failed";

/** One row in the document dashboard list. */
export interface Document {
  id: string;
  filename: string;
  version: number;
  status: DocumentStatus;
  /** ISO 8601 datetime string from the API, e.g. "2026-06-01T12:00:00Z" */
  updated_at: string;
}

/** A source chunk the AI used to ground its answer. */
export interface Citation {
  document_id: string;
  filename: string;
  chunk_text: string;
  page?: number | null;
}

/** Body sent when the user submits a chat message. */
export interface ChatRequest {
  message: string;
  /** Omit or null to start a new conversation. */
  conversation_id?: string | null;
}

/** SSE events from POST /chat */
export type ChatStreamEvent =
  | { type: 'token'; content: string }
  | { type: 'tool'; name: string; status: string; query?: string }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'done'; conversation_id: string }
  | { type: 'error'; message: string };

/** Simple liveness check — confirms the API is running. */
export interface HealthResponse {
  status: string;
}

/** Returned after a successful multipart upload. */
export interface UploadResponse {
  document_ids: string[];
}

/** One row in the conversation sidebar / list. */
export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

/** A single message in a conversation thread. */
export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  citations?: Citation[] | null;
  created_at: string;
}

/** Full conversation with message history. */
export interface ConversationDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
}
