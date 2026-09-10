import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '@/lib/api'
import { logout } from '@/lib/auth'
import { listNotifications, markAllNotificationsRead, markNotificationRead } from '@/lib/notifications'
import type { AppNotification } from '@/types'

/**
 * 헤더 알림 — 목록·안읽음 수·읽음 처리
 *
 * 종 아이콘의 배지와 드롭다운 목록이 같은 데이터를 봐야 해서 Header에서 한 번만
 * 부르고 AlertsDropdown에는 props로 내린다.
 *
 * 읽음 처리는 낙관적으로 화면을 먼저 바꾸고, 실패하면 서버 상태로 되돌린다.
 *
 * `enabled`가 false면 조회하지 않는다 — 관리자 화면에는 종 아이콘이 없어서
 * 굳이 요청을 보낼 필요가 없다.
 */
export function useNotifications(enabled = true) {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(enabled)
  const [error, setError] = useState('')

  const handleError = useCallback((e: unknown, fallback: string) => {
    if (e instanceof ApiError && e.status === 401) {
      logout()
      navigate('/login', { replace: true })
      return
    }
    setError(e instanceof ApiError ? e.message : fallback)
  }, [navigate])

  const refresh = useCallback(async () => {
    if (!enabled) return
    try {
      const data = await listNotifications()
      setNotifications(data.notifications)
      setUnreadCount(data.unreadCount)
      setError('')
    } catch (e) {
      handleError(e, '알림을 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }, [enabled, handleError])

  useEffect(() => {
    refresh()
  }, [refresh])

  const markRead = useCallback(async (id: string) => {
    const target = notifications.find(n => n.id === id)
    if (!target || target.isRead) return

    setNotifications(prev => prev.map(n => (n.id === id ? { ...n, isRead: true } : n)))
    setUnreadCount(prev => Math.max(0, prev - 1))
    try {
      await markNotificationRead(id)
    } catch {
      // 낙관적 갱신이 틀렸을 수 있으니 서버 상태를 다시 받아온다
      refresh()
    }
  }, [notifications, refresh])

  const markAllRead = useCallback(async () => {
    if (unreadCount === 0) return

    setNotifications(prev => prev.map(n => (n.isRead ? n : { ...n, isRead: true })))
    setUnreadCount(0)
    try {
      await markAllNotificationsRead()
    } catch (e) {
      handleError(e, '읽음 처리에 실패했습니다.')
      refresh()
    }
  }, [unreadCount, refresh, handleError])

  return { notifications, unreadCount, loading, error, refresh, markRead, markAllRead }
}

export type NotificationsValue = ReturnType<typeof useNotifications>
