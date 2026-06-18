import type { Citation } from '../types/api'

interface CitationCardProps {
  citation: Citation
  index: number
}

export default function CitationCard({ citation, index }: CitationCardProps) {
  const pageLabel = citation.page != null ? `p. ${citation.page}` : null

  return (
    <details className="group border-l-2 border-line pl-3 open:border-accent">
      <summary className="cursor-pointer list-none text-sm text-muted marker:content-none hover:text-ink [&::-webkit-details-marker]:hidden">
        <span className="font-mono text-[10px] text-faint">[{index + 1}]</span>{' '}
        <span className="text-ink">{citation.filename}</span>
        {pageLabel && (
          <span className="ml-1 font-mono text-[10px] text-faint">{pageLabel}</span>
        )}
      </summary>
      <p className="mt-2 text-sm leading-relaxed text-muted whitespace-pre-wrap">
        {citation.chunk_text}
      </p>
    </details>
  )
}
