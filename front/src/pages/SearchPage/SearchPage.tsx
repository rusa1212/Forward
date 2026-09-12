import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { listAnnouncements } from '@/lib/announcements'
import { SORT_OPTIONS, STATUS_TYPES } from '@/constants'
import { useFavoritesContext } from '@/contexts/FavoritesContext'
import { useKeywordsContext } from '@/contexts/KeywordsContext'
import { useDetailModal } from '@/hooks/useDetailModal'
import ResultsTable from './ResultsTable'
import Pagination from './Pagination'
import type { Announcement, SortType, StatusType } from '@/types'

const PAGE_SIZE = 8

export default function SearchPage() {
  const { favorites, toggleFavorite } = useFavoritesContext()
  const { keywords } = useKeywordsContext()
  const { openDetail } = useDetailModal()
  const [searchParams] = useSearchParams()

  // 대시보드 "매칭된 공고 전체보기"(?matched=1)로 들어온 경우 — 내 키워드 전체를
  // OR로 매칭한 결과를 보여준다. 진입 시 한 번만 확인하고, 이후엔 화면 안의
  // "전체 검색으로 전환" 버튼으로만 끈다.
  const [matchedMode, setMatchedMode] = useState(() => searchParams.get('matched') === '1')

  // 랜딩페이지 검색바에서 ?q=검색어로 들어온 경우 그대로 검색어로 반영한다.
  const initialQuery = searchParams.get('q') ?? ''
  const [keyword, setKeyword] = useState(initialQuery)
  const [query, setQuery] = useState(initialQuery)
  const [selectedStatus, setSelectedStatus] = useState<'전체' | StatusType>('전체')
  const [sort, setSort] = useState<SortType>('latest')
  const [currentPage, setCurrentPage] = useState(1)

  const [results, setResults] = useState<Announcement[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [reloadTick, setReloadTick] = useState(0)

  const keywordNames = keywords.map(k => k.name)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setErrorMsg('')
    listAnnouncements({
      q: matchedMode ? undefined : (query || undefined),
      keywords: matchedMode ? keywordNames : undefined,
      statusLabel: selectedStatus === '전체' ? undefined : selectedStatus,
      sort,
      page: currentPage,
      pageSize: PAGE_SIZE,
    })
      .then(({ items, meta }) => {
        if (cancelled) return
        setResults(items)
        setTotal(meta.total)
      })
      .catch(() => {
        if (!cancelled) setErrorMsg('공고를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.')
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchedMode, query, selectedStatus, sort, currentPage, reloadTick])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const runSearch = () => {
    setMatchedMode(false)
    setQuery(keyword.trim())
    setCurrentPage(1)
  }

  const resetFilters = () => {
    setMatchedMode(false)
    setKeyword('')
    setQuery('')
    setSelectedStatus('전체')
    setSort('latest')
    setCurrentPage(1)
  }

  const exitMatchedMode = () => {
    setMatchedMode(false)
    setCurrentPage(1)
  }

  const selectStatus = (s: '전체' | StatusType) => {
    setSelectedStatus(s)
    setCurrentPage(1)
  }

  const selectSort = (s: SortType) => {
    setSort(s)
    setCurrentPage(1)
  }

  const hasSearched = query.trim().length > 0

  return (
    <div className="max-w-[1200px] mx-auto px-8 py-7 space-y-5">
      {/* 페이지 헤더 */}
      <div className="rise rise-1">
        <h1 className="text-[22px] font-extrabold text-strong tracking-[-0.3px]">공고 검색</h1>
        <p className="mt-1 text-[13px] text-muted2">구독 키워드에 없는 새로운 분야도 자유롭게 탐색할 수 있습니다.</p>
      </div>

      {/* 필터 카드 */}
      <div className="rise rise-2 bg-surface border border-line rounded-xl px-7 py-5 space-y-4">
        <div className="flex items-center gap-2.5">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted2" strokeWidth={2} />
            <input
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && runSearch()}
              placeholder="공고명을 입력하세요"
              autoFocus
              className="w-full h-[46px] pl-10 pr-4 bg-white border border-line rounded-[10px] text-sm text-strong placeholder:text-muted2 focus:outline-none focus:border-primary2 focus:ring-2 focus:ring-primary2/20 transition-all"
            />
          </div>
          <button
            onClick={runSearch}
            className="pressable h-[46px] px-6 rounded-[10px] bg-primary2 hover:bg-primary-hover active:bg-primary-pressed text-white text-sm font-bold transition-colors shrink-0"
          >
            검색
          </button>
        </div>

        <div className="flex items-center justify-between flex-wrap gap-3">
          {/* iOS형 상태 세그먼트 */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-muted2">상태</span>
            <div className="flex items-center bg-[#eef2f6] rounded-full p-[3px]">
              {STATUS_TYPES.map(s => (
                <button
                  key={s}
                  onClick={() => selectStatus(s)}
                  className={cn(
                    'h-7 px-3.5 rounded-full text-[13px] transition-all whitespace-nowrap',
                    selectedStatus === s ? 'bg-white text-strong font-semibold shadow-seg' : 'text-sub font-medium hover:text-strong'
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* 정렬 — 우측 */}
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-muted2">정렬</span>
            <div className="flex items-center bg-[#eef2f6] rounded-full p-[3px]">
              {SORT_OPTIONS.map(([value, label]) => (
                <button
                  key={value}
                  onClick={() => selectSort(value)}
                  className={cn(
                    'h-7 px-3.5 rounded-full text-[13px] transition-all whitespace-nowrap',
                    sort === value ? 'bg-white text-strong font-semibold shadow-seg' : 'text-sub font-medium hover:text-strong'
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 매칭 모드 배너 — 대시보드 "전체 보기"로 진입한 경우 */}
      {matchedMode && (
        <div className="rise flex items-center gap-3 px-4 py-3 bg-soft rounded-[10px]">
          <span className="flex-1 text-[13px] text-primary2">
            내 구독 키워드 <strong className="font-bold">{keywordNames.join(', ') || '없음'}</strong>에 매칭된 공고를 보고 있습니다
          </span>
          <button
            onClick={exitMatchedMode}
            className="pressable shrink-0 flex items-center gap-1 text-xs font-semibold text-primary2 hover:text-primary-hover transition-colors"
          >
            <X className="w-3 h-3" strokeWidth={2.4} />
            전체 검색으로 전환
          </button>
        </div>
      )}

      {/* 결과 카드 */}
      <div className="rise rise-3 bg-surface border border-line rounded-xl overflow-hidden">
        <div className="px-7 py-4 border-b border-line flex items-center justify-between">
          {matchedMode ? (
            <span className="text-sm text-body">
              내 키워드 매칭 공고 <strong className="text-base text-strong font-bold tabular-nums">{total}</strong>
              <span className="whitespace-nowrap">건</span>
            </span>
          ) : hasSearched ? (
            <span className="text-sm text-body">
              <strong className="text-strong font-bold">"{query}"</strong> 검색 결과{' '}
              <strong className="text-strong font-bold tabular-nums">{total}</strong>
              <span className="whitespace-nowrap">건</span>
            </span>
          ) : (
            <span className="text-sm text-body">
              전체 공고 <strong className="text-strong font-bold tabular-nums">{total}</strong>
              <span className="whitespace-nowrap">건</span>
            </span>
          )}
          <span className="text-xs text-muted2 whitespace-nowrap">매일 09:00 업데이트</span>
        </div>

        {loading ? (
          <div className="py-24 text-center text-sm text-muted2">공고를 불러오는 중...</div>
        ) : errorMsg ? (
          <div className="py-24 text-center">
            <p className="text-sm text-danger font-medium">{errorMsg}</p>
            <button onClick={() => setReloadTick(t => t + 1)} className="mt-3 text-xs text-primary2 font-medium hover:underline">다시 시도</button>
          </div>
        ) : results.length === 0 ? (
          <div className="py-24 text-center">
            {hasSearched ? (
              <>
                <p className="text-sm font-medium text-body">"{query}"에 대한 결과가 없습니다.</p>
                <p className="mt-1 text-xs text-muted2">다른 키워드로 다시 검색해보세요.</p>
              </>
            ) : (
              <p className="text-sm font-medium text-body">표시할 공고가 없습니다.</p>
            )}
            <button onClick={resetFilters} className="mt-3 text-xs text-primary2 font-medium hover:underline">검색 초기화</button>
          </div>
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
