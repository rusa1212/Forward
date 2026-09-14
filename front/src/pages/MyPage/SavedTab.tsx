import { useEffect, useState } from 'react'
import { listSavedAnnouncements } from '@/lib/announcements'
import { useFavoritesContext } from '@/contexts/FavoritesContext'
import { useKeywordsContext } from '@/contexts/KeywordsContext'
import { useDetailModal } from '@/hooks/useDetailModal'
import ResultsTable from '@/pages/SearchPage/ResultsTable'
import type { Announcement } from '@/types'

/** 마이페이지 "저장한 공고" 탭 — 대시보드 KPI 카드/즐겨찾기에서 저장한 공고를 다시 찾아보는 화면. */
export default function SavedTab() {
  const { favorites, toggleFavorite } = useFavoritesContext()
  const { keywords } = useKeywordsContext()
  const { openDetail } = useDetailModal()

  const [rows, setRows] = useState<Announcement[]>([])
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [reloadTick, setReloadTick] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setErrorMsg('')
    listSavedAnnouncements()
      .then(saved => { if (!cancelled) setRows(saved.map(row => row.announcement)) })
      .catch(() => { if (!cancelled) setErrorMsg('저장한 공고를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [reloadTick])

  // 이 화면에 뜬 공고는 전부 이미 저장돼 있는 상태이므로, 토글은 곧 저장 해제다 —
  // 성공하면 바로 목록에서도 지워 "저장 해제했는데 목록엔 남아있는" 혼란을 없앤다.
  const handleToggleFavorite = async (id: string) => {
    await toggleFavorite(id)
    setRows(prev => prev.filter(a => a.id !== id))
  }

  return (
    <div className="bg-surface border border-line rounded-xl overflow-hidden">
      <div className="px-7 py-4 border-b border-line flex items-center gap-2">
        <h3 className="text-[15px] font-bold text-strong">저장한 공고</h3>
        <span className="px-2 py-0.5 rounded-full bg-soft text-primary2 text-[11px] font-bold tabular-nums whitespace-nowrap">{rows.length}건</span>
      </div>

      {loading ? (
        <div className="py-24 text-center text-sm text-muted2">불러오는 중...</div>
      ) : errorMsg ? (
        <div className="py-24 text-center">
          <p className="text-sm text-danger font-medium">{errorMsg}</p>
          <button onClick={() => setReloadTick(t => t + 1)} className="mt-3 text-xs text-primary2 font-medium hover:underline">다시 시도</button>
        </div>
      ) : rows.length === 0 ? (
        <div className="py-24 text-center">
          <p className="text-sm font-medium text-body">아직 저장한 공고가 없습니다.</p>
          <p className="mt-1 text-xs text-muted2">공고 검색이나 대시보드에서 별 아이콘을 눌러 저장해보세요.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <ResultsTable rows={rows} favorites={favorites} keywords={keywords} onOpenDetail={openDetail} onToggleFavorite={handleToggleFavorite} />
        </div>
      )}
    </div>
  )
}
