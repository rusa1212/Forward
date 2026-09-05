import { api } from './api'
import type { AppNotification } from '@/types'

/**
 * 헤더 알림 — 목록 조회 + 읽음 처리.
 * back/app/api/v1/notifications.py. 모두 토큰 필요. (docs/api-contract-v1.md 9절)
 *
 * 이 API는 notification_logs를 조회·읽음 처리만 한다. 알림을 쌓는 파이프라인은
 * core/scheduler.py의 매일 06시 수집에 이미 연결돼 있고, 수집 API 키가 없으면
 * 새 공고가 없어 알림도 쌓이지 않는다.
 */

interface NotificationListResponse {
  unreadCount: number
  notifications: AppNotification[]
}

/** 최신순 최대 50건 + 안읽은 개수. 알림이 없으면 빈 배열이지 오류가 아니다. */
export async function listNotifications(): Promise<NotificationListResponse> {
  const { data } = await api.get<NotificationListResponse>('/notifications')
  return {
    unreadCount: data?.unreadCount ?? 0,
    notifications: data?.notifications ?? [],
  }
}

/**
 * 1건 읽음. 이미 읽은 알림을 다시 처리해도 오류가 아니다(멱등).
 * 없는 알림이거나 남의 알림이면 ApiError(404, 'NOTIFICATION_NOT_FOUND')
 */
export function markNotificationRead(id: string) {
  return api
    .post<{ message: string }>(`/notifications/${encodeURIComponent(id)}/read`)
    .then(({ data }) => data)
}

/** 안읽은 알림 전부 읽음. count는 이번에 처리된 건수다. */
export function markAllNotificationsRead() {
  return api
    .post<{ message: string; count: number }>('/notifications/read-all')
    .then(({ data }) => data)
}
