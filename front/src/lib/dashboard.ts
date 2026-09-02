import { api } from './api'
import { mapAnnouncement } from './announcements'
import type { Announcement } from '@/types'

/** back/app/api/v1/dashboard.py의 GET /dashboard/summary가 내려주는 필드. matched/saved는
 * announcements.py._serialize()와 동일한 형태라 mapAnnouncement()를 그대로 재사용한다. */
interface ApiDashboardSummary {
  counts: { matched: number; newToday: number; urgent: number; saved: number }
  matched: Parameters<typeof mapAnnouncement>[0][]
  saved: Parameters<typeof mapAnnouncement>[0][]
}

export interface DashboardSummary {
  counts: ApiDashboardSummary['counts']
  matched: Announcement[]
  saved: Announcement[]
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get<ApiDashboardSummary>('/dashboard/summary')
  return {
    counts: data.counts,
    matched: data.matched.map(mapAnnouncement),
    saved: data.saved.map(mapAnnouncement),
  }
}
