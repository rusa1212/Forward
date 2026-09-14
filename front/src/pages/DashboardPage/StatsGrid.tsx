import { useNavigate } from 'react-router-dom'
import { useCountUp } from '@/hooks/useCountUp'

/** KPI 스트립 — 단일 서피스를 헤어라인으로 4분할, 수치 위계 차등 (30/800 vs 24/700) */
export default function KpiStrip({ matchedCount, newTodayCount, urgentCount, savedCount }: {
  matchedCount: number
  newTodayCount: number
  urgentCount: number
  savedCount: number
}) {
  const navigate = useNavigate()
  const matched = useCountUp(matchedCount)
  const newToday = useCountUp(newTodayCount)
  const urgent = useCountUp(urgentCount)
  const saved = useCountUp(savedCount)

  return (
    <div className="rise rise-2 bg-surface border border-line rounded-xl grid grid-cols-2 lg:grid-cols-4 divide-x divide-line overflow-hidden">
      <button
        onClick={() => navigate('/search?matched=1')}
        className="pressable min-w-[160px] box-border px-7 py-5 text-left hover:bg-subtle transition-colors"
      >
        <p className="text-[13px] font-medium text-body">매칭 공고</p>
        <p className="mt-1.5 text-[30px] font-extrabold text-strong tabular-nums leading-none">
          {matched}<span className="text-sm font-semibold text-muted2 ml-1">건</span>
        </p>
        <p className="mt-2 text-xs text-muted2">구독 키워드 기준 누적</p>
      </button>
      <button
        onClick={() => navigate('/search?matched=1')}
        className="pressable min-w-[160px] box-border px-7 py-5 text-left hover:bg-subtle transition-colors"
      >
        <p className="text-[13px] font-medium text-body">오늘 신규</p>
        <p className="mt-1.5 text-[30px] font-extrabold text-strong tabular-nums leading-none">
          {newToday}<span className="text-sm font-semibold text-muted2 ml-1">건</span>
        </p>
        <p className="mt-2 text-xs font-medium text-success whitespace-nowrap">오늘 09:00 수집분</p>
      </button>
      <button
        onClick={() => navigate(`/search?matched=1&status=${encodeURIComponent('마감임박')}`)}
        className="pressable min-w-[160px] box-border px-7 py-5 text-left hover:bg-subtle transition-colors"
      >
        <p className="text-[13px] font-medium text-body">마감 임박</p>
        <p className="mt-1.5 text-2xl font-bold text-warning tabular-nums leading-none">
          {urgent}<span className="text-sm font-semibold text-muted2 ml-1">건</span>
        </p>
        <p className="mt-2 text-xs text-muted2 whitespace-nowrap">D-3 이내</p>
      </button>
      <button
        onClick={() => navigate('/mypage/saved')}
        className="pressable min-w-[160px] box-border px-7 py-5 text-left hover:bg-subtle transition-colors"
      >
        <p className="text-[13px] font-medium text-body">저장한 공고</p>
        <p className="mt-1.5 text-2xl font-bold text-body tabular-nums leading-none">
          {saved}<span className="text-sm font-semibold text-muted2 ml-1">건</span>
        </p>
        <p className="mt-2 text-xs text-muted2 whitespace-nowrap">즐겨찾기 목록 보기</p>
      </button>
    </div>
  )
}
