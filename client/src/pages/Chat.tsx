import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  deleteConversation,
  getConversation,
  getConversations,
  streamChat,
} from '../api/client'
import type { Citation, ConversationSummary, ConversationVisibility } from '../types/api'
import ChatMessage, { type ChatMessageData } from '../components/ChatMessage'
import ConversationSidebar from '../components/ConversationSidebar'
import LlmModeToggle from '../components/LlmModeToggle'
import { useAuth } from '../context/AuthContext'

function newId() {
  return crypto.randomUUID()
}

export default function Chat() {
  const { user } = useAuth()
  const { conversationId: routeId } = useParams()
  const navigate = useNavigate()

  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [conversationsLoading, setConversationsLoading] = useState(true)
  const [messages, setMessages] = useState<ChatMessageData[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [threadMeta, setThreadMeta] = useState<{
    startedBy?: string
    visibility?: ConversationVisibility
    canDelete?: boolean
  } | null>(null)
  const [newThreadVisibility, setNewThreadVisibility] =
    useState<ConversationVisibility>('team')
  const bottomRef = useRef<HTMLDivElement>(null)

  const activeId = routeId ?? null

  const refreshConversations = useCallback(async () => {
    try {
      const list = await getConversations()
      setConversations(list)
    } catch {
      /* sidebar empty state handles it */
    } finally {
      setConversationsLoading(false)
    }
  }, [])

  const loadConversation = useCallback(async (id: string) => {
    setError(null)
    try {
      const detail = await getConversation(id)
      setThreadMeta({
        startedBy: detail.started_by?.display_name,
        visibility: detail.visibility,
        canDelete: detail.can_delete,
      })
      setMessages(
        detail.messages.map((m) => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          citations: m.citations ?? undefined,
          authorName:
            m.role === 'user' ? m.author?.display_name ?? undefined : undefined,
        })),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load thread')
      setMessages([])
    }
  }, [])

  useEffect(() => {
    void refreshConversations()
  }, [refreshConversations])

  useEffect(() => {
    if (routeId) {
      void loadConversation(routeId)
    } else {
      setMessages([])
      setThreadMeta(null)
    }
  }, [routeId, loadConversation])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, status])

  function handleNewChat() {
    navigate('/chat')
    setMessages([])
    setThreadMeta(null)
    setNewThreadVisibility('team')
    setError(null)
    setStatus(null)
  }

  function handleSelectConversation(id: string) {
    navigate(`/chat/${id}`)
  }

  async function handleDeleteConversation(id: string) {
    setError(null)
    try {
      await deleteConversation(id)
      await refreshConversations()
      if (activeId === id) handleNewChat()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete thread')
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setError(null)
    setStatus(null)
    setLoading(true)

    const userMsgId = newId()
    const assistantMsgId = newId()

    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        role: 'user',
        content: text,
        authorName: user?.display_name,
      },
      { id: assistantMsgId, role: 'assistant', content: '', streaming: true },
    ])

    let answer = ''
    let citations: Citation[] = []

    try {
      for await (const event of streamChat({
        message: text,
        conversation_id: activeId,
        visibility: activeId ? undefined : newThreadVisibility,
      })) {
        if (event.type === 'token') {
          answer += event.content
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? { ...m, content: answer, streaming: true }
                : m,
            ),
          )
        } else if (event.type === 'tool') {
          setStatus(
            event.query
              ? `Retrieving passages for “${event.query}”`
              : 'Searching the library',
          )
        } else if (event.type === 'citations') {
          citations = event.citations
        } else if (event.type === 'error') {
          setError(event.message)
        } else if (event.type === 'done') {
          navigate(`/chat/${event.conversation_id}`, { replace: true })
          void refreshConversations()
        }
      }

      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: answer, citations, streaming: false }
            : m,
        ),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setMessages((prev) => prev.filter((m) => m.id !== assistantMsgId))
    } finally {
      setLoading(false)
      setStatus(null)
    }
  }

  return (
    <div className="flex h-screen flex-col md:flex-row">
      <ConversationSidebar
        conversations={conversations}
        activeId={activeId}
        loading={conversationsLoading}
        onSelect={handleSelectConversation}
        onNew={handleNewChat}
        onDelete={(id) => void handleDeleteConversation(id)}
      />

      <div className="flex min-h-0 flex-1 flex-col">
        <header className="shrink-0 border-b border-line px-5 py-4 md:px-8">
          <h1 className="font-display text-2xl font-semibold tracking-tight">
            Ask
          </h1>
          <p className="mt-0.5 text-sm text-muted">
            Questions are answered only from documents in your library.
          </p>
          {threadMeta?.startedBy && (
            <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
              Started by {threadMeta.startedBy}
              {threadMeta.visibility === 'private' && ' · Private'}
            </p>
          )}
          <LlmModeToggle />
        </header>

        {error && (
          <p
            role="alert"
            className="mx-5 mt-4 rounded-md border border-accent/30 bg-accent-soft px-3 py-2 text-sm text-accent md:mx-8"
          >
            {error}
          </p>
        )}

        <div className="flex-1 overflow-y-auto px-5 py-6 md:px-8">
          {messages.length === 0 && !loading && (
            <div className="mx-auto max-w-lg pt-16 text-center">
              <p className="font-display text-xl text-ink">
                What do you need from the library?
              </p>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                The assistant searches your uploaded files before answering.
                Past threads appear in the column on the left.
              </p>
            </div>
          )}

          <div className="mx-auto max-w-2xl space-y-6">
            {messages.map((m) => (
              <ChatMessage key={m.id} message={m} />
            ))}
            {status && (
              <p className="font-mono text-xs text-faint">{status}…</p>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <form
          onSubmit={(e) => void handleSubmit(e)}
          className="shrink-0 border-t border-line bg-surface px-5 py-4 md:px-8"
        >
          {!activeId && (
            <div className="mx-auto mb-3 flex max-w-2xl items-center gap-3">
              <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
                New thread
              </span>
              <div className="inline-flex rounded-md border border-line p-0.5" role="group">
                {(['team', 'private'] as const).map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setNewThreadVisibility(option)}
                    className={[
                      'rounded px-3 py-1 font-mono text-[11px] uppercase tracking-wide',
                      newThreadVisibility === option
                        ? 'bg-accent-soft font-medium text-ink'
                        : 'text-muted hover:text-ink',
                    ].join(' ')}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="mx-auto flex max-w-2xl gap-2">
            <label htmlFor="chat-input" className="sr-only">
              Your question
            </label>
            <input
              id="chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a policy, product, process…"
              disabled={loading}
              className="flex-1 border border-line bg-paper px-4 py-3 text-sm text-ink placeholder:text-faint focus:border-accent focus:outline-none disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-accent px-5 py-3 text-sm font-medium text-surface transition-colors hover:bg-accent-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:opacity-40"
            >
              {loading ? '…' : 'Send'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
