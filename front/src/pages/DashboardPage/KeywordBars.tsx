import { useNavigate } from 'react-router-dom'
import type { Keyword } from '@/types'

/** 키워드별 매칭 — 단일 블루 바 (투명도 사다리 금지), 트랙 6px */
export default function KeywordBars({ keywords }: { keywords: Keyword[] }) {
  const navigate = useNavigate()
  const max = Math.max(1, ...keywords.map(k => k.matchCount))

  return (
    <div className="rise rise-3 h-full bg-surface border border-line rounded-xl px-7 py-5 flex flex-col">
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-bold text-strong">키워드별 매칭</h3>
        <button onClick={() => navigate('/mypage/keywords')} className="text-xs font-medium text-primary2 hover:text-primary-hover">
          관리 ›
        </button>
      </div>
      {keywords.length === 0 ? (
        <div className="flex-1 py-10 text-center text-sm text-muted2">
          등록된 키워드가 없습니다.
          <button onClick={() => navigate('/mypage/keywords')} className="block mx-auto mt-2 text-xs text-primary2 hover:underline">
            키워드 등록하기
          </button>
        </div>
      ) : (
        <div className="mt-4 space-y-4">
          {keywords.map(k => (
            <div key={k.id}>
              <div className="flex items-baseline justify-between mb-1.5">
                <span className="text-[13px] font-medium text-strong">{k.name}</span>
                <span className="text-xs text-muted2 tabular-nums whitespace-nowrap">{k.matchCount}건</span>
              </div>
              <div className="h-1.5 rounded-full bg-[#f2f4f7] overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary2 transition-[width] duration-500"
                  style={{ width: `${Math.round((k.matchCount / max) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
