import { ChevronLeft, ChevronRight } from 'lucide-react'

export default function Pagination({ currentPage, totalPages, onChange }: {
  currentPage: number
  totalPages: number
  onChange: (page: number) => void
}) {
  if (totalPages <= 1) return null

  return (
    <div className="px-7 py-3.5 border-t border-line flex items-center justify-center gap-1.5">
      <button
        onClick={() => onChange(Math.max(1, currentPage - 1))}
        disabled={currentPage === 1}
        aria-label="이전 페이지"
        className="pressable w-7 h-7 rounded-full flex items-center justify-center text-sub hover:bg-subtle disabled:opacity-30 transition-colors"
      >
        <ChevronLeft className="w-3.5 h-3.5" strokeWidth={2} />
      </button>
      {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={`pressable w-7 h-7 rounded-full text-[13px] tabular-nums transition-colors ${
            currentPage === p ? 'bg-soft text-primary2 font-bold' : 'text-sub font-medium hover:bg-subtle'
          }`}
        >
          {p}
        </button>
      ))}
      <button
        onClick={() => onChange(Math.min(totalPages, currentPage + 1))}
        disabled={currentPage === totalPages}
        aria-label="다음 페이지"
        className="pressable w-7 h-7 rounded-full flex items-center justify-center text-sub hover:bg-subtle disabled:opacity-30 transition-colors"
      >
        <ChevronRight className="w-3.5 h-3.5" strokeWidth={2} />
      </button>
    </div>
  )
}
