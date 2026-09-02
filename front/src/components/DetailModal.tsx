import { useEffect, useState } from 'react'
import { getAnnouncementDetail } from '@/lib/announcements'
import StatusBadge from '@/components/common/StatusBadge'
import { useFavoritesContext } from '@/contexts/FavoritesContext'
import { useDetailModal } from '@/hooks/useDetailModal'
import type { Announcement } from '@/types'

/** 공고 상세 모달 — `?detail=<id>` 쿼리스트링으로 열리고 닫힌다. */
export default function DetailModal() {
  const { detailId, closeDetail } = useDetailModal()
  const { isFavorite, toggleFavorite } = useFavoritesContext()
  const [remote, setRemote] = useState<Announcement | null>(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    setRemote(null)
    setNotFound(false)
    if (detailId === null) return
    let cancelled = false
    getAnnouncementDetail(detailId)
      .then(result => { if (!cancelled) setRemote(result) })
      .catch(() => { if (!cancelled) setNotFound(true) })
    return () => { cancelled = true }
  }, [detailId])

  if (detailId === null) return null

  const a = remote
  if (!a) {
    if (!notFound) return null
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={closeDetail}>
        <div className="bg-white rounded-2xl shadow-2xl p-8 text-center" onClick={e => e.stopPropagation()}>
          <p className="text-sm text-gray-600 font-medium mb-4">존재하지 않는 공고입니다.</p>
          <button onClick={closeDetail} className="text-sm text-[#457b9d] hover:underline font-medium">닫기</button>
        </div>
      </div>
    )
  }

  const onClose = closeDetail
  const onToggleFavorite = () => toggleFavorite(a.id)
  const favorite = isFavorite(a.id)

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-100">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <StatusBadge status={a.status} />
                {a.field && <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">{a.field}</span>}
              </div>
              <h2 className="text-base font-bold text-gray-800 leading-snug">{a.title}</h2>
            </div>
            <div className="flex items-center gap-1 flex-shrink-0">
              <button onClick={onToggleFavorite} className={`p-2 rounded-xl hover:bg-gray-100 transition-colors ${favorite ? "text-yellow-400" : "text-gray-200 hover:text-gray-400"}`} title="즐겨찾기">
                <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </button>
              <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div className="px-6 py-5 space-y-4">
          {/* D-Day Banner */}
          {a.dday !== null && a.dday >= 0 && a.dday <= 7 && (
            <div className={`rounded-xl p-3.5 flex items-center gap-3 ${a.dday <= 1 ? 'bg-red-50 border border-red-200' : 'bg-amber-50 border border-amber-200'}`}>
              <svg className={`w-4 h-4 flex-shrink-0 ${a.dday <= 1 ? 'text-red-500' : 'text-amber-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className={`text-sm font-semibold ${a.dday <= 1 ? 'text-red-700' : 'text-amber-700'}`}>
                {a.dday === 0 ? '오늘이 마감일입니다!' : `마감까지 ${a.dday}일 남았습니다.`}
              </span>
            </div>
          )}

          {/* Info table — mirrors the reference layout */}
          <div className="border border-gray-200 rounded-xl overflow-hidden text-sm">
            {/* Row 1 */}
            <div className="grid grid-cols-2 border-b border-gray-100">
              <div className="flex items-center gap-2 px-4 py-3 border-r border-gray-100">
                <span className="text-xs text-gray-400 whitespace-nowrap">출처</span>
                <span className="font-medium text-gray-800">{a.announcementType}</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-3">
                <span className="text-xs text-gray-400 whitespace-nowrap">공고기관명</span>
                <span className="font-medium text-gray-800">{a.org}</span>
              </div>
            </div>
            {/* Row 2 */}
            <div className="grid grid-cols-3 border-b border-gray-100">
              <div className="flex items-center gap-2 px-4 py-3 border-r border-gray-100">
                <span className="text-xs text-gray-400 whitespace-nowrap">공고일</span>
                <span className="font-medium text-gray-800">{a.postedDate}</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-3 border-r border-gray-100">
                <span className="text-xs text-gray-400 whitespace-nowrap">마감일</span>
                <span className="font-medium text-gray-800">{a.deadline}</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-3">
                <span className="text-xs text-gray-400 whitespace-nowrap">접수마감시간</span>
                <span className="font-medium text-gray-800">{a.deadlineTime}</span>
              </div>
            </div>
            {/* Row 3 */}
            {a.contact && (
              <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100">
                <span className="text-xs text-gray-400 whitespace-nowrap">문의처</span>
                <span className="font-medium text-[#457b9d]">{a.contact}</span>
              </div>
            )}
            {/* Row 4 */}
            {a.projectName && (
              <div className="flex items-center gap-2 px-4 py-3">
                <span className="text-xs text-gray-400 whitespace-nowrap">사업명</span>
                <span className="font-medium text-gray-800">{a.projectName}</span>
              </div>
            )}
          </div>

          {/* 공고 원문 */}
          {a.originalText && (
            <div className="border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-500">공고 원문</span>
                <span className="text-[10px] text-gray-400">일부 발췌</span>
              </div>
              <div className="px-4 py-4 max-h-48 overflow-y-auto">
                <pre className="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap font-sans">{a.originalText}</pre>
              </div>
            </div>
          )}
        </div>

        <div className="px-6 pb-6 flex gap-3">
          {a.originalUrl && (
            <a
              href={a.originalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-2 bg-[#1d3557] text-white rounded-xl py-2.5 text-sm font-semibold hover:bg-[#16293f] transition-colors"
            >
              본 공고 바로가기
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          )}
          <button onClick={onClose} className="flex-1 border border-gray-200 text-gray-600 rounded-xl py-2.5 text-sm font-semibold hover:bg-gray-50 transition-colors">
            닫기
          </button>
        </div>
      </div>
    </div>
  )
}
