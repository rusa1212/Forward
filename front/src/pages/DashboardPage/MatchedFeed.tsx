import { useNavigate } from 'react-router-dom'
import StatusBadge from '@/components/common/StatusBadge'
import { getKeywordColor, matchKeywords } from '@/lib/keywordMatch'
import type { Announcement } from '@/types'

export default function MatchedFeed({ matchedAds, newTodayCount, keywordNames, onOpenDetail }: {
  matchedAds: Announcement[]
  newTodayCount: number
  keywordNames: string[]
  onOpenDetail: (id: string) => void
}) {
  const navigate = useNavigate()

  return (
    <div className="rise rise-4 h-full bg-surface border border-line rounded-xl overflow-hidden flex flex-col">
      <div className="px-7 pt-5 pb-3.5 flex items-center justify-between border-b border-line">
        <div className="flex items-center gap-2">
          <h3 className="text-[15px] font-bold text-strong">오늘 매칭된 공고</h3>
          {newTodayCount > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-soft text-primary2 text-[11px] font-bold whitespace-nowrap">NEW {newTodayCount}</span>
          )}
        </div>
        <span className="text-xs text-muted2 whitespace-nowrap">매일 09:00 업데이트</span>
      </div>

      {matchedAds.length === 0 ? (
        <div className="py-16 text-center text-sm text-muted2">오늘 매칭된 공고가 없습니다.</div>
      ) : (
        <div>
          {matchedAds.slice(0, 5).map((a, i, arr) => {
            const matched = matchKeywords(a, keywordNames)
            return (
              <button
                key={a.id}
                onClick={() => onOpenDetail(a.id)}
                className={`w-full px-7 py-[13px] flex items-center justify-between gap-4 text-left hover:bg-subtle transition-colors ${i < arr.length - 1 ? 'border-b border-line' : ''}`}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-[15px] font-semibold text-strong truncate">{a.title}</p>
                  <div className="mt-1.5 flex items-center gap-2">
                    <span className="text-xs text-body">{a.org}</span>
                    {matched.slice(0, 3).map(k => {
                      const c = getKeywordColor(k)
                      return (
                        <span key={k} className={`text-[11px] font-medium px-2 py-0.5 rounded ${c.bg} ${c.text} whitespace-nowrap`}>{k}</span>
                      )
                    })}
                  </div>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1">
                  <StatusBadge status={a.status} />
                  <span className="text-xs text-muted2 whitespace-nowrap tabular-nums">
                    ~{a.deadline}{a.dday !== null && a.dday >= 0 ? ` · D-${a.dday === 0 ? 'day' : a.dday}` : ''}
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      )}

      <div className="mt-auto px-7 py-3 border-t border-line">
        <button onClick={() => navigate('/search')} className="text-[13px] font-medium text-primary2 hover:text-primary-hover">
          전체 {matchedAds.length}건 보기 ›
        </button>
      </div>
    </div>
  )
}
