import { useNavigate } from 'react-router-dom'
import { ANNOUNCEMENTS } from '@/data/mock/announcements'
import { MY_KEYWORDS } from '@/constants'
import { useFavoritesContext } from '@/contexts/FavoritesContext'
import { useDetailModal } from '@/hooks/useDetailModal'
import StatsGrid from './StatsGrid'
import MatchedFeed from './MatchedFeed'
import SavedList from './SavedList'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { favorites } = useFavoritesContext()
  const { openDetail } = useDetailModal()

  const matchedAds = ANNOUNCEMENTS.filter(a =>
    a.relatedKeywords.some(k => MY_KEYWORDS.includes(k))
  )
  const newToday = matchedAds.filter(a => a.postedDate === '2024-02-15' || a.postedDate === '2024-02-13' || a.postedDate === '2024-02-12')
  const urgentAds = matchedAds.filter(a => a.dday >= 0 && a.dday <= 3)
  const favoriteList = ANNOUNCEMENTS.filter(a => favorites.has(a.id))

  return (
    <div className="max-w-7xl mx-auto">
      {/* Personalized header band */}
      <div className="bg-[#1d3557] px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-blue-200 text-xs font-medium mb-1">2024년 2월 15일 오전 9:00 기준 업데이트</p>
            <h1 className="text-white text-xl font-bold">안녕하세요, 김담당자님 👋</h1>
            <p className="text-blue-300 text-sm mt-1">오늘 등록 키워드에 매칭된 공고 <strong className="text-white">{matchedAds.length}건</strong>이 있습니다.</p>
          </div>
        </div>

        {/* Subscribed keywords */}
        <div className="mt-4 flex items-center gap-2 flex-wrap">
          <span className="text-blue-300 text-xs">구독 키워드</span>
          {MY_KEYWORDS.map(k => (
            <span key={k} className="bg-white/15 text-white text-xs px-2.5 py-1 rounded-full border border-white/20 font-medium">{k}</span>
          ))}
          <button onClick={() => navigate('/mypage/keywords')} className="text-blue-300 text-xs hover:text-white transition-colors underline underline-offset-2">+ 키워드 관리</button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Quick stats */}
        <StatsGrid
          matchedCount={matchedAds.length}
          newTodayCount={newToday.length}
          urgentCount={urgentAds.length}
          savedCount={favoriteList.length}
        />

        {/* Urgent alert strip */}
        {urgentAds.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-3.5 flex items-center gap-3">
            <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="text-sm text-red-700 font-medium">
              마감 임박 공고 {urgentAds.length}건 — {urgentAds.map(a => a.title.slice(0, 16) + '…').join(', ')}
            </p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-6">
          <MatchedFeed matchedAds={matchedAds} newToday={newToday} onOpenDetail={openDetail} />
          <SavedList favoriteList={favoriteList} onOpenDetail={openDetail} />
        </div>
      </div>
    </div>
  )
}
