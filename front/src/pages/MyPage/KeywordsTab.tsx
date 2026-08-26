import { useState } from 'react'
import { useKeywordsContext } from '@/contexts/KeywordsContext'

export default function KeywordsTab() {
  const { keywords, addKeyword, removeKeyword } = useKeywordsContext()
  const [newKeyword, setNewKeyword] = useState('')

  const handleAdd = () => {
    if (addKeyword(newKeyword)) setNewKeyword('')
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h3 className="text-sm font-semibold text-gray-800 mb-3">키워드 등록</h3>
        <div className="flex gap-2">
          <input
            value={newKeyword}
            onChange={e => setNewKeyword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            className="flex-1 border border-gray-200 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition"
            placeholder="키워드 입력 후 Enter 또는 등록"
          />
          <button onClick={handleAdd} className="bg-[#1d3557] text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-[#16293f] transition-colors">등록</button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-gray-100 flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-800">등록된 키워드</span>
          <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{keywords.length}개</span>
        </div>
        {keywords.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">등록된 키워드가 없습니다.</div>
        ) : (
          <div className="divide-y divide-gray-50">
            {keywords.map(kw => (
              <div key={kw.id} className="px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded-full font-semibold border border-blue-100">{kw.name}</span>
                  <span className="text-xs text-gray-400">매칭 공고 <strong className="text-gray-600">{kw.matchCount}</strong>건</span>
                </div>
                <button onClick={() => removeKeyword(kw.id)} className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
