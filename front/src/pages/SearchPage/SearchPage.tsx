import { useMemo, useState } from 'react'
import { ANNOUNCEMENTS } from '@/data/mock/announcements'
import { STATUS_TYPES } from '@/constants'
import { useFavoritesContext } from '@/contexts/FavoritesContext'
import { useDetailModal } from '@/hooks/useDetailModal'
import ResultsTable from './ResultsTable'
import Pagination from './Pagination'
import type { StatusType } from '@/types'

const PAGE_SIZE = 8

export default function SearchPage() {
  const { favorites } = useFavoritesContext()
  const { openDetail } = useDetailModal()
  const [keyword, setKeyword] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<'전체' | StatusType>('전체')
  const [currentPage, setCurrentPage] = useState(1)

  const searched = useMemo(() => {
    const kw = keyword.trim().toLowerCase()
    if (!kw) return ANNOUNCEMENTS
    return ANNOUNCEMENTS.filter(a =>
      a.title.toLowerCase().includes(kw) ||
      a.org.toLowerCase().includes(kw) ||
      a.relatedKeywords.some(k => k.toLowerCase().includes(kw))
    )
  }, [keyword])

  const filtered = useMemo(() =>
    selectedStatus === '전체' ? searched : searched.filter(a => a.status === selectedStatus)
  , [searched, selectedStatus])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paged = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const resetFilters = () => {
    setKeyword('')
    setSelectedStatus('전체')
    setCurrentPage(1)
  }

  const hasSearched = keyword.trim().length > 0

  return (
    <div className="max-w-7xl mx-auto">
      {/* Search hero */}
      <div className="bg-gradient-to-br from-[#f0f2f5] to-[#e8edf4] px-8 py-8 border-b border-gray-200">
        <p className="text-xs font-semibold text-[#457b9d] uppercase tracking-widest mb-2">공고 탐색</p>
        <h1 className="text-xl font-bold text-gray-800 mb-1">관심 있는 공고를 직접 찾아보세요</h1>
        <p className="text-sm text-gray-500 mb-6">키워드에 등록하지 않은 새로운 분야도 자유롭게 탐색할 수 있습니다.</p>

        <div className="flex gap-3 max-w-2xl">
          <div className="relative flex-1">
            <svg className="absolute left-4 top-3.5 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && setCurrentPage(1)}
              className="w-full bg-white border border-gray-300 shadow-sm rounded-2xl pl-11 pr-4 py-3 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition"
              placeholder="공고명, 기관명, 관심 키워드를 입력하세요"
              autoFocus
            />
          </div>
          <button
            onClick={() => setCurrentPage(1)}
            className="bg-[#1d3557] text-white px-7 py-3 rounded-2xl text-sm font-bold hover:bg-[#16293f] shadow-sm transition-colors"
          >
            검색
          </button>
          {keyword && (
            <button onClick={resetFilters} className="px-4 py-3 rounded-2xl text-sm text-gray-500 hover:text-gray-700 bg-white border border-gray-200 hover:bg-gray-50 transition-colors">
              초기화
            </button>
          )}
        </div>

        {/* Quick suggest chips — shown before search */}
        {!hasSearched && (
          <div className="mt-4 flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-400">추천 탐색어</span>
            {['바이오', '반도체', '교통', '물류', '교육', '탄소중립'].map(s => (
              <button key={s} onClick={() => { setKeyword(s); setCurrentPage(1) }} className="text-xs bg-white border border-gray-200 text-gray-600 px-3 py-1 rounded-full hover:border-[#457b9d] hover:text-[#457b9d] transition-colors">
                {s}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="p-6">
        {/* Results */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                {hasSearched ? (
                  <>
                    <span className="text-sm text-gray-600">
                      <strong className="text-gray-800">"{keyword}"</strong> 검색 결과 <strong className="text-gray-800">{filtered.length}</strong>건
                    </span>
                    {filtered.length > 0 && (
                      <span className="text-xs text-gray-400">클릭하면 상세 내용을 볼 수 있습니다</span>
                    )}
                  </>
                ) : (
                  <span className="text-sm text-gray-600">전체 공고 <strong className="text-gray-800">{filtered.length}</strong>건</span>
                )}
              </div>
              {selectedStatus !== '전체' && (
                <button onClick={() => { setSelectedStatus('전체'); setCurrentPage(1) }} className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1 transition-colors">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  상태 초기화
                </button>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-400 mr-1">상태</span>
              {STATUS_TYPES.map(s => {
                const count = s === '전체' ? searched.length : searched.filter(a => a.status === s).length
                return (
                  <button
                    key={s}
                    onClick={() => { setSelectedStatus(s); setCurrentPage(1) }}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors flex items-center gap-1 ${selectedStatus === s ? 'bg-[#1d3557] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                  >
                    {s}
                    <span className={`text-[10px] ${selectedStatus === s ? 'text-white/70' : 'text-gray-400'}`}>{count}</span>
                  </button>
                )
              })}
            </div>
          </div>

        {paged.length === 0 ? (
          <div className="py-24 text-center">
            <div className="w-14 h-14 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <p className="text-gray-500 text-sm font-medium">"{keyword}"에 대한 결과가 없습니다.</p>
            <p className="text-gray-400 text-xs mt-1">다른 키워드로 다시 검색해보세요.</p>
            <button onClick={resetFilters} className="mt-3 text-xs text-[#457b9d] hover:underline font-medium">검색 초기화</button>
          </div>
        ) : (
          <>
            <ResultsTable rows={paged} favorites={favorites} onOpenDetail={openDetail} />
            <Pagination currentPage={currentPage} totalPages={totalPages} onChange={setCurrentPage} />
          </>
        )}
        </div>
      </div>
    </div>
  )
}
