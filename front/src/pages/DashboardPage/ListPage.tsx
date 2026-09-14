import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { listAnnouncements } from '@/lib/announcements'
import { useFavoritesContext } from '@/contexts/FavoritesContext'
import { useKeywordsContext } from '@/contexts/KeywordsContext'
import { useDetailModal } from '@/hooks/useDetailModal'
import ResultsTable from '@/pages/SearchPage/ResultsTable'
import Pagination from '@/pages/SearchPage/Pagination'
import type { Announcement, StatusType } from '@/types'

const PAGE_SIZE = 10

type ListType = 'matched' | 'new' | 'urgent'

const CONFIG: Record<ListType, {
  title: string
  subtitle: string
  statusLabel?: StatusType
  collectedToday?: boolean
  sort: 'latest' | 'deadline'
}> = {
  matched: { title: '매칭 공고', subtitle: '구독 키워드에 매칭된 전체 공고입니다.', sort: 'latest' },
  new: { title: '오늘 매칭된 공고', subtitle: '오늘 새로 수집되어 구독 키워드에 매칭된 공고입니다.', collectedToday: true, sort: 'latest' },
  urgent: { title: '마감 임박', subtitle: '구독 키워드에 매칭된 공고 중 마감이 3일 이내로 다가온 공고입니다.', statusLabel: '마감임박', sort: 'deadline' },
}

function isListType(value: string | null): value is ListType {
  return value === 'matched' || value === 'new' || value === 'urgent'
}

/** 대시보드 KPI 카드(매칭 공고/오늘 매칭된 공고/마감 임박) 전용 결과 화면 — 검색 페이지를
 * 재사용하지 않고 독립된 페이지로 보여준다(?type=matched|new|urgent). */
export default function ListPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { favorites, toggleFavorite } = useFavoritesContext()
  const { keywords } = useKeywordsContext()
  const { openDetail } = useDetailModal()

  const type: ListType = isListType(searchParams.get('type')) ? (searchParams.get('type') as ListType) : 'matched'
  const config = CONFIG[type]
  const keywordNames = keywords.map(k => k.name)

  const [results, setResults] = useState<Announcement[]>([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [reloadTick, setReloadTick] = useState(0)

  useEffect(() => {
    setCurrentPage(1)
  }, [type])

  useEffect(() => {
    if (keywordNames.length === 0) {
      setResults([])
      setTotal(0)
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setErrorMsg('')
    listAnnouncements({
      keywords: keywordNames,
      statusLabel: config.statusLabel,
      collectedToday: config.collectedToday,
      sort: config.sort,
      page: currentPage,
      pageSize: PAGE_SIZE,
    })
      .then(({ items, meta }) => {
        if (cancelled) return
        setResults(items)
        setTotal(meta.total)
      })
      .catch(() => { if (!cancelled) setErrorMsg('공고를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, currentPage, reloadTick])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div className="max-w-[1200px] mx-auto px-8 py-7 space-y-5">
      <div className="rise rise-1">
        <h1 className="text-[22px] font-extrabold text-strong tracking-[-0.3px]">{config.title}</h1>
        <p className="mt-1 text-[13px] text-muted2">{config.subtitle}</p>
      </div>

      <div className="rise rise-2 bg-surface border border-line rounded-xl overflow-hidden">
        <div className="px-7 py-4 border-b border-line flex items-center justify-between">
          <span className="text-sm text-body">
            총 <strong className="text-strong font-bold tabular-nums">{total}</strong>건
          </span>
          <button onClick={() => navigate('/search')} className="text-xs text-primary2 hover:text-primary-hover font-medium whitespace-nowrap">
            전체 공고 검색 ›
          </button>
        </div>

        {keywordNames.length === 0 ? (
          <div className="py-24 text-center">
            <p className="text-sm font-medium text-body">등록된 구독 키워드가 없습니다.</p>
            <button onClick={() => navigate('/mypage/keywords')} className="mt-3 text-xs text-primary2 font-medium hover:underline">
              키워드 등록하러 가기
            </button>
          </div>
        ) : loading ? (
          <div className="py-24 text-center text-sm text-muted2">공고를 불러오는 중...</div>
        ) : errorMsg ? (
          <div className="py-24 text-center">
            <p className="text-sm text-danger font-medium">{errorMsg}</p>
            <button onClick={() => setReloadTick(t => t + 1)} className="mt-3 text-xs text-primary2 font-medium hover:underline">다시 시도</button>
          </div>
        ) : results.length === 0 ? (
          <div className="py-24 text-center text-sm text-muted2">해당하는 공고가 없습니다.</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <ResultsTable rows={results} favorites={favorites} keywords={keywords} onOpenDetail={openDetail} onToggleFavorite={toggleFavorite} />
            </div>
            <Pagination currentPage={currentPage} totalPages={totalPages} onChange={setCurrentPage} />
          </>
        )}
      </div>
    </div>
  )
}
