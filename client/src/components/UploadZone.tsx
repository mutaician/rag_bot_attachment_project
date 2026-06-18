import { useRef, useState } from 'react'

const ACCEPT = '.pdf,.txt,.md'

interface UploadZoneProps {
  onUpload: (files: File[]) => Promise<void>
  disabled?: boolean
}

export default function UploadZone({ onUpload, disabled }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  async function handleFiles(fileList: FileList | null) {
    if (!fileList?.length || disabled) return
    await onUpload(Array.from(fileList))
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        void handleFiles(e.dataTransfer.files)
      }}
      className={[
        'cursor-pointer border border-dashed px-6 py-12 text-center transition-colors',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
        dragOver
          ? 'border-accent bg-accent-soft'
          : 'border-line bg-paper hover:border-faint',
        disabled ? 'pointer-events-none opacity-50' : '',
      ].join(' ')}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        multiple
        className="hidden"
        onChange={(e) => void handleFiles(e.target.files)}
      />
      <p className="font-display text-lg text-ink">Add to library</p>
      <p className="mt-2 text-sm text-muted">
        Drop files here or click to browse — PDF, Markdown, plain text
      </p>
    </div>
  )
}
