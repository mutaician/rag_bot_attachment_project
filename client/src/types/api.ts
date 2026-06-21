/**
 * API contract — TypeScript mirror of server/app/schemas.py
 */

/** Indexing lifecycle for an uploaded document. */
export type DocumentStatus = "pending" | "indexing" | "ready" | "failed";

/** One row in the document dashboard list. */
export interface Document {
  id: string;
  filename: string;
  version: number;
  status: DocumentStatus;
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
  conversation_id?: string | null;
}

/** SSE events from POST /chat */
export type ChatStreamEvent =
  | { type: 'token'; content: string }
  | { type: 'tool'; name: string; status: string; query?: string }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'done'; conversation_id: string }
  | { type: 'error'; message: string };

export interface HealthResponse {
  status: string;
}

export interface UploadResponse {
  document_ids: string[];
}

export interface UserRef {
  id: string;
  username: string;
  display_name: string;
}

export interface AuthUser {
  id: string;
  username: string;
  display_name: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LlmModeResponse {
  mode: 'local' | 'cloud';
}

export interface SystemCapabilities {
  embed: boolean;
  local_chat: boolean;
  cloud_chat: boolean;
  cloud_configured: boolean;
}

/** One row in the conversation sidebar / list. */
export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  started_by?: UserRef | null;
}

/** A single message in a conversation thread. */
export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  citations?: Citation[] | null;
  created_at: string;
  author?: UserRef | null;
}

/** Full conversation with message history. */
export interface ConversationDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  started_by?: UserRef | null;
  messages: ConversationMessage[];
}
