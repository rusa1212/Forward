import { Star } from 'lucide-react'
import StatusBadge from '@/components/common/StatusBadge'
import { getKeywordColor, matchKeywords } from '@/lib/keywordMatch'
import type { Announcement, Keyword } from '@/types'

const GRID = 'grid grid-cols-[minmax(0,1fr)_170px_110px_76px_120px_40px] items-center gap-2'

export default function ResultsTable({ rows, favorites, keywords, onOpenDetail, onToggleFavorite }: {
  rows: Announcement[]
  favorites: Set<string>
  keywords: Keyword[]
  onOpenDetail: (id: string) => void
  onToggleFavorite: (id: string) => void
}) {
  const keywordNames = keywords.map(k => k.name)

  return (
    <div className="min-w-[860px]">
      {/* 컬럼 헤더 */}
      <div className={`${GRID} px-7 h-10 bg-thead border-b border-line`}>
        <span className="text-xs font-semibold text-muted2">공고명</span>
        <span className="text-xs font-semibold text-muted2">소관부처</span>
        <span className="text-xs font-semibold text-muted2">공고기관명</span>
        <span className="text-xs font-semibold text-muted2">상태</span>
        <span className="text-xs font-semibold text-muted2 text-right">마감</span>
        <span />
      </div>

      {rows.map((a, i) => (
        <div
          key={a.id}
          className={`${GRID} px-7 py-[13px] cursor-pointer hover:bg-subtle transition-colors ${i < rows.length - 1 ? 'border-b border-line' : ''}`}
          onClick={() => onOpenDetail(a.id)}
        >
          <div className="min-w-0 pr-4">
            <p className="text-[15px] font-semibold text-strong truncate">{a.title}</p>
            <div className="mt-1 flex items-center gap-1.5">
              {matchKeywords(a, keywordNames).slice(0, 3).map(k => {
                const c = getKeywordColor(k)
                return (
                  <span key={k} className={`text-[11px] font-medium px-2 py-0.5 rounded ${c.bg} ${c.text} whitespace-nowrap`}>{k}</span>
                )
              })}
            </div>
          </div>
          <span className="text-[13px] text-body truncate pr-2">{a.org}</span>
          <span className="text-xs text-muted2 truncate">{a.announcementType}</span>
          <StatusBadge status={a.status} />
          <span className="text-[13px] text-body text-right whitespace-nowrap tabular-nums">
            ~{a.deadline}
            {a.dday !== null && a.dday >= 0 && (
              <span className={a.dday <= 1 ? 'text-danger font-semibold' : a.dday <= 3 ? 'text-warning font-semibold' : ''}>
                {' '}· D-{a.dday === 0 ? 'day' : a.dday}
              </span>
            )}
          </span>
          <button
            onClick={e => { e.stopPropagation(); onToggleFavorite(a.id) }}
            aria-label={favorites.has(a.id) ? '저장 해제' : '공고 저장'}
            className="pressable justify-self-end p-1 group"
          >
            <Star
              className={`w-[18px] h-[18px] transition-colors ${
                favorites.has(a.id) ? 'text-star fill-star' : 'text-faint group-hover:text-warning'
              }`}
              strokeWidth={1.8}
            />
          </button>
        </div>
      ))}
    </div>
  )
}
