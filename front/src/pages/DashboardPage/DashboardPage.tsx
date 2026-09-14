import { useEffect, useState } from 'react'
import { Check, ChevronDown, ChevronUp, EyeOff, Plus, RotateCcw, Settings2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { getDashboardSummary, type DashboardSummary } from '@/lib/dashboard'
import { useKeywordsContext } from '@/contexts/KeywordsContext'
import { useDetailModal } from '@/hooks/useDetailModal'
import KpiStrip from './StatsGrid'
import TrendChart from './TrendChart'
import KeywordBars from './KeywordBars'
import MatchedFeed from './MatchedFeed'
import UrgentPanel from './UrgentPanel'

const EMPTY_SUMMARY: DashboardSummary = {
  counts: { matched: 0, newToday: 0, urgent: 0, saved: 0 },
  matched: [],
  urgent: [],
  saved: [],
}

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

/* ===== 위젯 커스텀(순서/숨기기) — localStorage에 저장 ===== */
type WidgetId = 'kpi' | 'trend' | 'keywords' | 'matched' | 'urgent'

const DEFAULT_ORDER: WidgetId[] = ['kpi', 'trend', 'keywords', 'matched', 'urgent']

const WIDGET_LABEL: Record<WidgetId, string> = {
  kpi: '요약 지표',
  trend: '매칭 추이',
  keywords: '키워드별 매칭',
  matched: '오늘 매칭된 공고',
  urgent: '마감 임박',
}

/* 3컬럼 그리드에서 각 위젯이 차지하는 폭 */
const WIDGET_SPAN: Record<WidgetId, string> = {
  kpi: 'lg:col-span-3',
  trend: 'lg:col-span-2',
  keywords: 'lg:col-span-1',
  matched: 'lg:col-span-2',
  urgent: 'lg:col-span-1',
}

const LAYOUT_KEY = 'forward-dashboard-layout-v1'

interface Layout {
  order: WidgetId[]
  hidden: WidgetId[]
}

function loadLayout(): Layout {
  try {
    const raw = localStorage.getItem(LAYOUT_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as Layout
      const order = parsed.order.filter(id => DEFAULT_ORDER.includes(id))
      for (const id of DEFAULT_ORDER) if (!order.includes(id)) order.push(id)
      const hidden = (parsed.hidden ?? []).filter(id => DEFAULT_ORDER.includes(id))
      return { order, hidden }
    }
  } catch { /* 저장값이 깨졌으면 기본값 사용 */ }
  return { order: [...DEFAULT_ORDER], hidden: [] }
}

function saveLayout(layout: Layout) {
  try { localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout)) } catch { /* 프라이빗 모드 등 */ }
}

export default function DashboardPage() {
  const { keywords } = useKeywordsContext()
  const { openDetail } = useDetailModal()

  const [summary, setSummary] = useState<DashboardSummary>(EMPTY_SUMMARY)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState('')
  const [layout, setLayout] = useState<Layout>(loadLayout)
  const [editing, setEditing] = useState(false)

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

  const updateLayout = (next: Layout) => {
    setLayout(next)
    saveLayout(next)
  }

  const move = (id: WidgetId, dir: -1 | 1) => {
    const order = [...layout.order]
    const i = order.indexOf(id)
    const j = i + dir
    if (j < 0 || j >= order.length) return
    ;[order[i], order[j]] = [order[j], order[i]]
    updateLayout({ ...layout, order })
  }

  const hide = (id: WidgetId) => updateLayout({ ...layout, hidden: [...layout.hidden, id] })
  const show = (id: WidgetId) => updateLayout({ ...layout, hidden: layout.hidden.filter(h => h !== id) })
  const resetLayout = () => updateLayout({ order: [...DEFAULT_ORDER], hidden: [] })

  const keywordNames = keywords.map(k => k.name)
  const { counts, matched, urgent: urgentAds } = summary

  const now = new Date()
  const dateLabel = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, '0')}.${String(now.getDate()).padStart(2, '0')} (${WEEKDAYS[now.getDay()]})`

  const widgetBody: Record<WidgetId, React.ReactNode> = {
    kpi: <KpiStrip matchedCount={counts.matched} newTodayCount={counts.newToday} urgentCount={counts.urgent} savedCount={counts.saved} />,
    trend: <TrendChart />,
    keywords: <KeywordBars keywords={keywords} />,
    matched: <MatchedFeed matchedAds={matched} newTodayCount={counts.newToday} keywordNames={keywordNames} onOpenDetail={openDetail} />,
    urgent: <UrgentPanel urgentAds={urgentAds} onOpenDetail={openDetail} />,
  }

  const visible = layout.order.filter(id => !layout.hidden.includes(id))
  const isDefault = layout.hidden.length === 0 && layout.order.join() === DEFAULT_ORDER.join()

  return (
    <div className="max-w-[1200px] mx-auto px-8 py-7 space-y-5">
      {/* 페이지 헤더 */}
      <div className="rise rise-1 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-[22px] font-extrabold text-strong tracking-[-0.3px]">대시보드</h1>
          <p className="mt-1 text-[13px] text-muted2">{dateLabel} · 구독 키워드 {keywords.length}개 기준</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[13px] text-muted2 whitespace-nowrap">마지막 수집 오늘 09:00</span>
          <button
            onClick={() => setEditing(e => !e)}
            className={cn(
              'pressable h-9 px-3.5 rounded-[10px] text-[13px] font-semibold flex items-center gap-1.5 transition-colors whitespace-nowrap',
              editing
                ? 'bg-primary2 text-white hover:bg-primary-hover'
                : 'bg-white border border-line text-body hover:bg-subtle'
            )}
          >
            {editing ? <Check className="w-3.5 h-3.5" strokeWidth={2.2} /> : <Settings2 className="w-3.5 h-3.5" strokeWidth={1.9} />}
            {editing ? '편집 완료' : '위젯 편집'}
          </button>
        </div>
      </div>

      {/* 편집 모드 안내 + 숨긴 위젯 복원 */}
      {editing && (
        <div className="rise flex items-center justify-between gap-4 flex-wrap px-4 py-3 bg-soft rounded-[10px]">
          <span className="text-[13px] text-primary2 font-medium">화살표로 위젯 순서를 바꾸고, 눈 아이콘으로 숨길 수 있어요. 설정은 이 브라우저에 저장됩니다.</span>
          <div className="flex items-center gap-2 flex-wrap">
            {layout.hidden.map(id => (
              <button
                key={id}
                onClick={() => show(id)}
                className="pressable h-7 px-3 rounded-full bg-white border border-line text-xs font-medium text-body hover:bg-subtle flex items-center gap-1 transition-colors"
              >
                <Plus className="w-3 h-3" strokeWidth={2.2} />
                {WIDGET_LABEL[id]}
              </button>
            ))}
            {!isDefault && (
              <button onClick={resetLayout} className="pressable h-7 px-3 rounded-full text-xs font-medium text-sub hover:text-strong flex items-center gap-1 transition-colors">
                <RotateCcw className="w-3 h-3" strokeWidth={2} />
                기본값 복원
              </button>
            )}
          </div>
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center text-sm text-muted2">대시보드를 불러오는 중...</div>
      ) : errorMsg ? (
        <div className="py-24 text-center">
          <p className="text-sm text-danger font-medium">{errorMsg}</p>
        </div>
      ) : visible.length === 0 ? (
        <div className="py-24 text-center text-sm text-muted2">
          모든 위젯이 숨겨져 있습니다.
          <button onClick={resetLayout} className="block mx-auto mt-2 text-xs text-primary2 font-medium hover:underline">기본값 복원</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {visible.map(id => {
            const idx = layout.order.indexOf(id)
            return (
              <div
                key={id}
                className={cn('relative min-w-0', WIDGET_SPAN[id], editing && 'rounded-xl outline-2 outline-dashed outline-primary2/35 outline-offset-4')}
              >
                {editing && (
                  <div className="absolute -top-3 right-4 z-10 flex items-center gap-0.5 bg-white border border-line rounded-full shadow-seg px-1 py-0.5">
                    <span className="text-[11px] font-semibold text-sub px-1.5 whitespace-nowrap">{WIDGET_LABEL[id]}</span>
                    <button
                      onClick={() => move(id, -1)}
                      disabled={idx === 0}
                      aria-label="위로 이동"
                      className="pressable p-1 rounded-full text-sub hover:bg-subtle hover:text-strong disabled:opacity-25 transition-colors"
                    >
                      <ChevronUp className="w-3.5 h-3.5" strokeWidth={2.2} />
                    </button>
                    <button
                      onClick={() => move(id, 1)}
                      disabled={idx === layout.order.length - 1}
                      aria-label="아래로 이동"
                      className="pressable p-1 rounded-full text-sub hover:bg-subtle hover:text-strong disabled:opacity-25 transition-colors"
                    >
                      <ChevronDown className="w-3.5 h-3.5" strokeWidth={2.2} />
                    </button>
                    <button
                      onClick={() => hide(id)}
                      aria-label={`${WIDGET_LABEL[id]} 숨기기`}
                      className="pressable p-1 rounded-full text-sub hover:bg-[rgba(240,68,56,0.08)] hover:text-danger transition-colors"
                    >
                      <EyeOff className="w-3.5 h-3.5" strokeWidth={1.9} />
                    </button>
                  </div>
                )}
                {widgetBody[id]}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
