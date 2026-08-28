import { useNavigate } from 'react-router-dom'
import StatusBadge from '@/components/common/StatusBadge'
import DDayBadge from '@/components/common/DDayBadge'
import { MY_KEYWORDS } from '@/constants'
import type { Announcement } from '@/types'

export default function MatchedFeed({ matchedAds, newToday, onOpenDetail }: {
  matchedAds: Announcement[]
  newToday: Announcement[]
  onOpenDetail: (id: string) => void
}) {
  const navigate = useNavigate()

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-gray-800">오늘 매칭된 공고</span>
            {newToday.length > 0 && (
              <span className="text-[10px] bg-[#1d3557] text-white px-1.5 py-0.5 rounded-full font-bold">NEW {newToday.length}</span>
            )}
          </div>
          <p className="text-[10px] text-gray-400 mt-0.5">내 구독 키워드 기준 자동 수집</p>
        </div>
        <span className="text-[10px] text-gray-400">매일 09:00 업데이트</span>
      </div>
      <div className="divide-y divide-gray-50">
        {matchedAds.slice(0, 5).map(a => {
          const isNew = newToday.some(n => n.id === a.id)
          return (
            <div key={a.id} onClick={() => onOpenDetail(a.id)} className="px-5 py-3.5 hover:bg-blue-50/30 cursor-pointer transition-colors group">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    {isNew && <span className="text-[9px] bg-blue-500 text-white px-1.5 py-0.5 rounded font-bold flex-shrink-0">NEW</span>}
                    <p className="text-sm text-gray-800 font-medium truncate group-hover:text-[#1d3557] transition-colors">{a.title}</p>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="text-xs text-gray-400">{a.org}</span>
                    <span className="text-gray-200">·</span>
                    <div className="flex gap-1">
                      {a.relatedKeywords.filter(k => MY_KEYWORDS.includes(k)).map(k => (
                        <span key={k} className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100/50">{k}</span>
                      ))}
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
        <button onClick={() => navigate('/search')} className="text-xs text-[#457b9d] hover:underline font-medium">
          전체 {matchedAds.length}건 보기 →
        </button>
      </div>
    </div>
  )
}
