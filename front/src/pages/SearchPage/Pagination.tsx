import { ChevronLeft, ChevronRight } from 'lucide-react'

const SIBLING_COUNT = 1

/**
 * 페이지 번호 목록을 만든다. 항상 첫/끝 페이지를 보여주고, 현재 페이지 주변
 * SIBLING_COUNT개만 펼치고 나머지는 '...'로 줄인다. 전체 페이지 수가 많아도
 * (예: 나라장터 대량 수집 후 수천 페이지) 렌더링되는 버튼 개수가 일정하게 유지된다.
 */
function buildPageNumbers(current: number, total: number): (number | '...')[] {
  const totalVisible = SIBLING_COUNT * 2 + 5 // 첫/끝 + 현재 + 양옆 + 말줄임 2칸 여유
  if (total <= totalVisible) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const left = Math.max(current - SIBLING_COUNT, 1)
  const right = Math.min(current + SIBLING_COUNT, total)
  const showLeftDots = left > 2
  const showRightDots = right < total - 1

  if (!showLeftDots && showRightDots) {
    const count = 3 + SIBLING_COUNT * 2
    return [...Array.from({ length: count }, (_, i) => i + 1), '...', total]
  }
  if (showLeftDots && !showRightDots) {
    const count = 3 + SIBLING_COUNT * 2
    return [1, '...', ...Array.from({ length: count }, (_, i) => total - count + i + 1)]
  }
  return [1, '...', ...Array.from({ length: right - left + 1 }, (_, i) => left + i), '...', total]
}

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
      {buildPageNumbers(currentPage, totalPages).map((p, i) =>
        p === '...' ? (
          <span key={`dots-${i}`} className="w-7 h-7 flex items-center justify-center text-[13px] text-faint select-none">
            ...
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p)}
            aria-label={`${p}페이지`}
            aria-current={currentPage === p ? 'page' : undefined}
            className={`pressable w-7 h-7 rounded-full text-[13px] tabular-nums transition-colors ${
              currentPage === p ? 'bg-soft text-primary2 font-bold' : 'text-sub font-medium hover:bg-subtle'
            }`}
          >
            {p}
          </button>
        )
      )}
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
