import { useNavigate } from 'react-router-dom'
import StatusBadge from '@/components/common/StatusBadge'
import DDayBadge from '@/components/common/DDayBadge'
import { getKeywordColor, matchKeywords } from '@/lib/keywordMatch'
import type { Announcement } from '@/types'

export default function MatchedFeed({ matchedAds, matchedCount, newTodayCount, keywordNames, onOpenDetail }: {
  matchedAds: Announcement[]
  /** 실제 매칭 총 건수. matchedAds는 BE가 최근 몇 건만 잘라서 내려주므로 개수 표시는 이 값을 써야 한다. */
  matchedCount: number
  newTodayCount: number
  keywordNames: string[]
  onOpenDetail: (id: string) => void
}) {
  const navigate = useNavigate()

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-gray-800">오늘 매칭된 공고</span>
            {newTodayCount > 0 && (
              <span className="text-[10px] bg-[#1d3557] text-white px-1.5 py-0.5 rounded-full font-bold">NEW {newTodayCount}</span>
            )}
          </div>
          <p className="text-[10px] text-gray-400 mt-0.5">내 구독 키워드 기준 자동 수집</p>
        </div>
        <span className="text-[10px] text-gray-400">매일 09:00 업데이트</span>
      </div>
      <div className="divide-y divide-gray-50">
        {matchedAds.slice(0, 5).map(a => {
          const matched = matchKeywords(a, keywordNames)
          return (
            <div key={a.id} onClick={() => onOpenDetail(a.id)} className="px-5 py-3.5 hover:bg-blue-50/30 cursor-pointer transition-colors group">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <p className="text-sm text-gray-800 font-medium truncate group-hover:text-[#1d3557] transition-colors">{a.title}</p>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="text-xs text-gray-400">{a.org}</span>
                    <span className="text-gray-200">·</span>
                    <div className="flex gap-1">
                      {matched.map(k => {
                        const c = getKeywordColor(k)
                        return (
                          <span key={k} className={`text-[10px] ${c.bg} ${c.text} px-1.5 py-0.5 rounded border ${c.border}`}>{k}</span>
                        )
                      })}
                    </div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 space-y-1">
                  <StatusBadge status={a.status} />
                  <p className="text-[10px] text-gray-400">{a.deadline}</p>
                  <DDayBadge dday={a.dday} />
                </div>
              </div>
            </div>
          )
        })}
      </div>
      <div className="px-5 py-3 border-t border-gray-100 bg-gray-50/50">
        <button onClick={() => navigate('/search?matched=1')} className="text-xs text-[#457b9d] hover:underline font-medium">
          전체 {matchedCount}건 보기 →
        </button>
      </div>
    </div>
  )
}
