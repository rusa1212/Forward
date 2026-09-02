import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboardSummary, type DashboardSummary } from '@/lib/dashboard'
import { getName } from '@/lib/auth'
import { useKeywordsContext } from '@/contexts/KeywordsContext'
import { useDetailModal } from '@/hooks/useDetailModal'
import StatsGrid from './StatsGrid'
import MatchedFeed from './MatchedFeed'
import SavedList from './SavedList'

const EMPTY_SUMMARY: DashboardSummary = {
  counts: { matched: 0, newToday: 0, urgent: 0, saved: 0 },
  matched: [],
  saved: [],
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const { keywords } = useKeywordsContext()
  const { openDetail } = useDetailModal()

  const [summary, setSummary] = useState<DashboardSummary>(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setErrorMsg('')
    getDashboardSummary()
      .then(result => { if (!cancelled) setSummary(result) })
      .catch(() => { if (!cancelled) setErrorMsg('대시보드 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const keywordNames = keywords.map(k => k.name)
  const { counts, matched, saved } = summary
  const urgentAds = matched.filter(a => a.dday !== null && a.dday >= 0 && a.dday <= 3)

  return (
    <div className="max-w-7xl mx-auto">
      {/* Personalized header band */}
      <div className="bg-[#1d3557] px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-white text-xl font-bold">안녕하세요, {getName()}님 👋</h1>
            <p className="text-blue-300 text-sm mt-1">오늘 등록 키워드에 매칭된 공고 <strong className="text-white">{counts.matched}건</strong>이 있습니다.</p>
          </div>
        </div>

        {/* Subscribed keywords */}
        <div className="mt-4 flex items-center gap-2 flex-wrap">
          <span className="text-blue-300 text-xs">구독 키워드</span>
          {keywordNames.map(k => (
            <span key={k} className="bg-white/15 text-white text-xs px-2.5 py-1 rounded-full border border-white/20 font-medium">{k}</span>
          ))}
          <button onClick={() => navigate('/mypage/keywords')} className="text-blue-300 text-xs hover:text-white transition-colors underline underline-offset-2">+ 키워드 관리</button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {loading ? (
          <div className="py-24 text-center text-gray-400 text-sm">대시보드를 불러오는 중...</div>
        ) : errorMsg ? (
          <div className="py-24 text-center text-red-500 text-sm font-medium">{errorMsg}</div>
        ) : (
          <>
            {/* Quick stats */}
            <StatsGrid
              matchedCount={counts.matched}
              newTodayCount={counts.newToday}
              urgentCount={counts.urgent}
              savedCount={counts.saved}
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
              <MatchedFeed matchedAds={matched} newTodayCount={counts.newToday} keywordNames={keywordNames} onOpenDetail={openDetail} />
              <SavedList favoriteList={saved} onOpenDetail={openDetail} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
