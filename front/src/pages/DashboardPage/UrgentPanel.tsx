import type { Announcement } from '@/types'

/** 마감 임박 — 좌측 D-n 강조(D-1 danger, D-2/3 warning) */
export default function UrgentPanel({ urgentAds, onOpenDetail }: {
  urgentAds: Announcement[]
  onOpenDetail: (id: string) => void
}) {
  return (
    <div className="rise rise-4 h-full bg-surface border border-line rounded-xl overflow-hidden flex flex-col">
      <div className="px-7 pt-5 pb-3.5 border-b border-line">
        <h3 className="text-[15px] font-bold text-strong">마감 임박</h3>
      </div>
      {urgentAds.length === 0 ? (
        <div className="flex-1 py-14 text-center text-sm text-muted2">D-3 이내 공고가 없습니다.</div>
      ) : (
        <div>
          {urgentAds.map((a, i, arr) => (
            <button
              key={a.id}
              onClick={() => onOpenDetail(a.id)}
              className={`w-full px-7 py-[13px] flex items-start gap-4 text-left hover:bg-subtle transition-colors ${i < arr.length - 1 ? 'border-b border-line' : ''}`}
            >
              <span className={`shrink-0 text-base font-bold tabular-nums whitespace-nowrap ${a.dday !== null && a.dday <= 1 ? 'text-danger' : 'text-warning'}`}>
                D-{a.dday === 0 ? 'day' : a.dday}
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold text-strong truncate">{a.title}</span>
                <span className="block mt-1 text-xs text-muted2 truncate">{a.org} · ~{a.deadline}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
