import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { useKeywordsContext } from '@/contexts/KeywordsContext'

const GRID = 'grid grid-cols-[minmax(0,1fr)_110px_64px] items-center gap-2'

export default function KeywordsTab() {
  const { keywords, addKeyword, removeKeyword, loading, error } = useKeywordsContext()
  const [newKeyword, setNewKeyword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleAdd = async () => {
    if (!newKeyword.trim() || submitting) return
    setSubmitting(true)
    const added = await addKeyword(newKeyword)
    setSubmitting(false)
    if (added) setNewKeyword('')
  }

  return (
    <div className="space-y-5">
      {/* 키워드 테이블 */}
      <div className="bg-surface border border-line rounded-xl overflow-hidden">
        <div className="px-7 py-4 border-b border-line flex items-center gap-2">
          <h3 className="text-[15px] font-bold text-strong">구독 키워드</h3>
          <span className="px-2 py-0.5 rounded-full bg-soft text-primary2 text-[11px] font-bold tabular-nums whitespace-nowrap">{keywords.length}개</span>
        </div>

        <div className="overflow-x-auto">
          <div className="min-w-[420px]">
            <div className={`${GRID} px-7 h-10 bg-thead border-b border-line`}>
              <span className="text-xs font-semibold text-muted2">키워드</span>
              <span className="text-xs font-semibold text-muted2 text-center">최근 30일</span>
              <span className="text-xs font-semibold text-muted2 text-center">삭제</span>
            </div>

            {loading ? (
              <div className="py-14 text-center text-sm text-muted2">불러오는 중...</div>
            ) : keywords.length === 0 ? (
              <div className="py-14 text-center text-sm text-muted2">등록된 키워드가 없습니다. 아래에서 첫 키워드를 추가해 보세요.</div>
            ) : (
              keywords.map((kw, i, arr) => (
                <div key={kw.id} className={`${GRID} px-7 py-3.5 hover:bg-subtle transition-colors ${i < arr.length - 1 ? 'border-b border-line' : ''}`}>
                  <span className="justify-self-start px-3 py-1 rounded-full bg-[#f2f4f7] text-strong text-[13px] font-semibold whitespace-nowrap">
                    {kw.name}
                  </span>
                  <span className="text-[13px] text-body text-center tabular-nums whitespace-nowrap">{kw.matchCount}건</span>
                  <button
                    onClick={() => removeKeyword(kw.id)}
                    aria-label={`${kw.name} 삭제`}
                    className="pressable justify-self-center p-1.5 rounded-lg text-faint hover:text-danger hover:bg-[rgba(240,68,56,0.06)] transition-colors"
                  >
                    <Trash2 className="w-4 h-4" strokeWidth={1.8} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 키워드 추가 */}
      <div className="bg-surface border border-line rounded-xl px-7 py-5">
        <h3 className="text-[15px] font-bold text-strong">키워드 추가</h3>
        <p className="mt-1 text-xs text-muted2">등록한 키워드로 매일 09:00 신규 공고를 찾아 알려드립니다.</p>
        <div className="mt-3 flex items-center gap-2">
          <input
            value={newKeyword}
            onChange={e => setNewKeyword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            placeholder="키워드 입력 후 Enter 또는 추가"
            className="flex-1 h-[46px] px-3.5 bg-white border border-line rounded-[10px] text-sm text-strong placeholder:text-muted2 focus:outline-none focus:border-primary2 focus:ring-2 focus:ring-primary2/20 transition-all"
          />
          <button
            onClick={handleAdd}
            disabled={submitting || !newKeyword.trim()}
            className="pressable h-[46px] px-6 rounded-[10px] bg-primary2 hover:bg-primary-hover text-white text-sm font-bold transition-colors disabled:opacity-40 shrink-0"
          >
            추가
          </button>
        </div>
        {error && <p className="mt-2 text-xs text-danger">{error}</p>}
      </div>
    </div>
  )
}
