import StatusBadge from '@/components/common/StatusBadge'
import DDayBadge from '@/components/common/DDayBadge'
import type { Announcement } from '@/types'

export default function SavedList({ favoriteList, onOpenDetail }: {
  favoriteList: Announcement[]
  onOpenDetail: (id: number) => void
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-gray-800">저장한 공고</span>
          <span className="text-xs bg-yellow-50 text-yellow-600 px-2 py-0.5 rounded-full border border-yellow-100">{favoriteList.length}건</span>
        </div>
        <p className="text-[10px] text-gray-400 mt-0.5">즐겨찾기로 저장한 공고 목록</p>
      </div>
      {favoriteList.length === 0 ? (
        <div className="py-14 text-center">
          <p className="text-gray-300 text-2xl mb-2">☆</p>
          <p className="text-sm text-gray-400">저장한 공고가 없습니다.</p>
          <p className="text-xs text-gray-300 mt-1">공고 상세에서 별표를 눌러 저장하세요</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-50">
          {favoriteList.map(a => (
            <div key={a.id} onClick={() => onOpenDetail(a.id)} className="px-5 py-3.5 hover:bg-yellow-50/30 cursor-pointer transition-colors group">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <svg className="w-3 h-3 text-yellow-400 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    <p className="text-sm text-gray-800 font-medium truncate group-hover:text-[#1d3557] transition-colors">{a.title}</p>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1 ml-4">
                    <span className="text-xs text-gray-400">{a.org}</span>
                    <span className="text-gray-200">·</span>
                    <span className="text-xs text-gray-400">{a.field}</span>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 space-y-1">
                  <StatusBadge status={a.status} />
                  <DDayBadge dday={a.dday} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
