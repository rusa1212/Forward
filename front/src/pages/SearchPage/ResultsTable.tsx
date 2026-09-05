import StatusBadge from '@/components/common/StatusBadge'
import DDayBadge from '@/components/common/DDayBadge'
import { getKeywordColor, matchKeywords } from '@/lib/keywordMatch'
import type { Announcement, Keyword } from '@/types'

export default function ResultsTable({ rows, favorites, keywords, onOpenDetail }: {
  rows: Announcement[]
  favorites: Set<string>
  keywords: Keyword[]
  onOpenDetail: (id: string) => void
}) {
  const keywordNames = keywords.map(k => k.name)

  return (
    <table className="w-full">
      <thead>
        <tr className="bg-gray-50/80 border-b border-gray-100">
          <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500">공고명</th>
          <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 w-28">소관부처</th>
          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 w-24">공고기관명</th>
          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 w-20">상태</th>
          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 w-24">공고일</th>
          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 w-24">마감일</th>
          <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 w-16">D-Day</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((a, i) => (
          <tr
            key={a.id}
            onClick={() => onOpenDetail(a.id)}
            className={`hover:bg-blue-50/30 cursor-pointer transition-colors border-b border-gray-50 ${i === rows.length - 1 ? 'border-b-0' : ''}`}
          >
            <td className="px-5 py-3.5">
              <div className="flex items-center gap-1.5">
                {favorites.has(a.id) && (
                  <svg className="w-3.5 h-3.5 text-yellow-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                )}
                <p className="text-sm text-gray-800 font-medium">{a.title}</p>
              </div>
              <div className="flex gap-1 mt-1 ml-0.5">
                {matchKeywords(a, keywordNames).map(k => {
                  const c = getKeywordColor(k)
                  return (
                    <span key={k} className={`text-[10px] ${c.bg} ${c.text} px-1.5 py-0.5 rounded border ${c.border}`}>{k}</span>
                  )
                })}
              </div>
            </td>
            <td className="px-4 py-3.5 text-sm text-gray-600">{a.org}</td>
            <td className="px-4 py-3.5 text-center">
              <span className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">{a.announcementType}</span>
            </td>
            <td className="px-4 py-3.5 text-center"><StatusBadge status={a.status} /></td>
            <td className="px-4 py-3.5 text-center text-xs text-gray-400">{a.postedDate}</td>
            <td className="px-4 py-3.5 text-center text-xs text-gray-500">{a.deadline}</td>
            <td className="px-4 py-3.5 text-center"><DDayBadge dday={a.dday} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
