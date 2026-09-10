import { useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { useDetailModal } from '@/hooks/useDetailModal'
import type { NotificationsValue } from '@/hooks/useNotifications'
import { formatRelativeTime } from '@/lib/datetime'

/** 알림 종류별 배지 색. 알 수 없는 종류는 회색으로 떨어진다. */
const TYPE_STYLE: Record<string, string> = {
  신규매칭: 'bg-soft text-primary2',
  마감임박: 'bg-[rgba(247,144,9,0.12)] text-warning',
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
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: -4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: 'spring', bounce: 0, duration: 0.3 }}
      style={{ transformOrigin: 'top right' }}
      className="absolute top-12 right-0 w-80 bg-surface rounded-xl border border-line shadow-float z-50 overflow-hidden"
    >
      <div className="px-4 py-3 border-b border-line flex items-center justify-between">
        <span className="font-semibold text-strong text-sm">
          알림
          {unreadCount > 0 && <span className="ml-1.5 text-xs text-primary2 font-bold tabular-nums">{unreadCount}</span>}
        </span>
        <button
          onClick={markAllRead}
          disabled={unreadCount === 0}
          className="text-xs text-primary2 hover:text-primary-hover disabled:text-faint disabled:cursor-default transition-colors"
        >
          모두 읽음
        </button>
      </div>

      <div className="divide-y divide-line max-h-72 overflow-y-auto">
        {loading && (
          <div className="px-4 py-10 text-center text-xs text-muted2">알림을 불러오는 중입니다...</div>
        )}

        {!loading && error && (
          <div className="px-4 py-8 text-center">
            <p className="text-xs text-danger">{error}</p>
            <button onClick={refresh} className="mt-2 text-xs text-primary2 hover:text-primary-hover">
              다시 시도
            </button>
          </div>
        )}

        {!loading && !error && notifications.length === 0 && (
          <div className="px-4 py-10 text-center">
            <p className="text-xs text-muted2">받은 알림이 없습니다.</p>
            <p className="text-[11px] text-faint mt-1">키워드를 등록하면 매칭되는 신규 공고를 알려드립니다.</p>
          </div>
        )}

        {!loading && !error && notifications.map(n => (
          <button
            key={n.id}
            onClick={() => handleClick(n.id, n.announcementId)}
            className={`w-full text-left px-4 py-3 hover:bg-subtle transition-colors ${n.isRead ? '' : 'bg-subtle/70'}`}
          >
            <div className="flex items-start gap-2">
              {!n.isRead && <span className="w-1.5 h-1.5 bg-primary2 rounded-full mt-1.5 flex-shrink-0" />}
              <div className={n.isRead ? 'ml-3.5' : ''}>
                <p className="text-xs text-strong font-medium leading-relaxed">{n.title}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${TYPE_STYLE[n.notifyType] ?? 'bg-[#f2f4f7] text-sub'}`}>
                    {n.keyword ?? n.notifyType}
                  </span>
                  <span className="text-[10px] text-muted2">{formatRelativeTime(n.createdAt)}</span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="px-4 py-2.5 border-t border-line text-center">
        <button onClick={() => { navigate('/mypage/alerts'); onClose() }} className="text-xs text-primary2 hover:text-primary-hover transition-colors">
          알림 설정 보기
        </button>
      </div>
    </motion.div>
  )
}
