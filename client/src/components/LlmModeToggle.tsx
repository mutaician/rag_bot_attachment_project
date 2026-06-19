import { useEffect, useState } from 'react'
import { getCapabilities, getLlmMode, setLlmMode } from '../api/client'
import type { LlmModeResponse, SystemCapabilities } from '../types/api'

export default function LlmModeToggle() {
  const [mode, setMode] = useState<LlmModeResponse['mode']>('local')
  const [caps, setCaps] = useState<SystemCapabilities | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [llm, capabilities] = await Promise.all([getLlmMode(), getCapabilities()])
        if (!cancelled) {
          setMode(llm.mode)
          setCaps(capabilities)
        }
      } catch {
        /* header still usable without toggle state */
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [])

  async function select(next: LlmModeResponse['mode']) {
    if (next === mode || saving) return
    setError(null)
    setSaving(true)
    try {
      const res = await setLlmMode(next)
      setMode(res.mode)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not switch mode')
    } finally {
      setSaving(false)
    }
  }

  const localDisabled = caps != null && !caps.local_chat
  const cloudDisabled = caps != null && (!caps.cloud_configured || !caps.cloud_chat)

  return (
    <div className="mt-3">
      <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
        Chat model (team)
      </p>
      <div
        className="mt-1.5 inline-flex rounded-md border border-line p-0.5"
        role="group"
        aria-label="LLM mode"
      >
        {(['local', 'cloud'] as const).map((option) => {
          const active = mode === option
          const disabled =
            loading ||
            saving ||
            (option === 'local' && localDisabled) ||
            (option === 'cloud' && cloudDisabled)
          return (
            <button
              key={option}
              type="button"
              disabled={disabled}
              onClick={() => void select(option)}
              className={[
                'rounded px-3 py-1 font-mono text-[11px] uppercase tracking-wide transition-colors',
                active ? 'bg-accent-soft font-medium text-ink' : 'text-muted hover:text-ink',
                disabled && !active ? 'opacity-40' : '',
              ].join(' ')}
            >
              {option}
            </button>
          )
        })}
      </div>
      {error && <p className="mt-1 text-xs text-accent">{error}</p>}
    </div>
  )
}
