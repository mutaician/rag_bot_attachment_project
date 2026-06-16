import { useRef, useState } from 'react'

const ACCEPT = '.pdf,.txt,.md'

interface UploadZoneProps {
  onUpload: (files: File[]) => Promise<void>
  disabled?: boolean
}

/**
 * Drag-and-drop + click-to-browse file upload area.
 */
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
        'cursor-pointer rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors',
        dragOver
          ? 'border-white bg-gray-800'
          : 'border-gray-700 bg-gray-900 hover:border-gray-500',
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
      <p className="font-medium text-gray-200">
        Drop files here or click to browse
      </p>
      <p className="mt-1 text-sm text-gray-500">PDF, Markdown, or plain text</p>
    </div>
  )
}
