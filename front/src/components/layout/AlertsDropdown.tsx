import { useNavigate } from 'react-router-dom'
import { useDetailModal } from '@/hooks/useDetailModal'
import type { NotificationsValue } from '@/hooks/useNotifications'
import { formatRelativeTime } from '@/lib/datetime'

/** 알림 종류별 배지 색. 알 수 없는 종류는 회색으로 떨어진다. */
const TYPE_STYLE: Record<string, string> = {
  신규매칭: 'bg-blue-100 text-blue-700',
  마감임박: 'bg-amber-100 text-amber-700',
}

export default function AlertsDropdown({ onClose, notifications: state }: {
  onClose: () => void
  notifications: NotificationsValue
}) {
  const navigate = useNavigate()
  const { openDetail } = useDetailModal()
  const { notifications, unreadCount, loading, error, refresh, markRead, markAllRead } = state

  /** 알림을 누르면 읽음 처리하고, 연결된 공고가 있으면 상세 모달을 연다. */
  const handleClick = (id: string, announcementId: string | null) => {
    markRead(id)
    if (announcementId) {
      openDetail(announcementId)
      onClose()
    }
  }

  return (
    <div className="absolute top-11 right-10 w-80 bg-white rounded-xl shadow-2xl border border-gray-100 z-50 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <span className="font-semibold text-gray-800 text-sm">
          알림
          {unreadCount > 0 && <span className="ml-1.5 text-xs text-[#457b9d] font-bold">{unreadCount}</span>}
        </span>
        <button
          onClick={markAllRead}
          disabled={unreadCount === 0}
          className="text-xs text-[#457b9d] hover:underline disabled:text-gray-300 disabled:no-underline disabled:cursor-default"
        >
          모두 읽음
        </button>
      </div>

      <div className="divide-y divide-gray-50 max-h-72 overflow-y-auto">
        {loading && (
          <div className="px-4 py-10 text-center text-xs text-gray-400">알림을 불러오는 중입니다...</div>
        )}

        {!loading && error && (
          <div className="px-4 py-8 text-center">
            <p className="text-xs text-red-600">{error}</p>
            <button onClick={refresh} className="mt-2 text-xs text-[#457b9d] hover:underline">
              다시 시도
            </button>
          </div>
        )}

        {!loading && !error && notifications.length === 0 && (
          <div className="px-4 py-10 text-center">
            <p className="text-xs text-gray-400">받은 알림이 없습니다.</p>
            <p className="text-[11px] text-gray-300 mt-1">키워드를 등록하면 매칭되는 신규 공고를 알려드립니다.</p>
          </div>
        )}

        {!loading && !error && notifications.map(n => (
          <button
            key={n.id}
            onClick={() => handleClick(n.id, n.announcementId)}
            className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${n.isRead ? '' : 'bg-blue-50/40'}`}
          >
            <div className="flex items-start gap-2">
              {!n.isRead && <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0" />}
              <div className={n.isRead ? 'ml-3.5' : ''}>
                <p className="text-xs text-gray-800 font-medium leading-relaxed">{n.title}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${TYPE_STYLE[n.notifyType] ?? 'bg-gray-100 text-gray-600'}`}>
                    {n.keyword ?? n.notifyType}
                  </span>
                  <span className="text-[10px] text-gray-400">{formatRelativeTime(n.createdAt)}</span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="px-4 py-2.5 border-t border-gray-100 text-center">
        <button onClick={() => { navigate('/mypage/alerts'); onClose() }} className="text-xs text-[#457b9d] hover:underline">
          알림 설정 보기
        </button>
      </div>
    </div>
  )
}
