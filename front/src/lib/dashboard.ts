import { api } from './api'
import { mapAnnouncement } from './announcements'
import type { Announcement } from '@/types'

/** back/app/api/v1/dashboard.py의 GET /dashboard/summary가 내려주는 필드. matched/saved는
 * announcements.py._serialize()와 동일한 형태라 mapAnnouncement()를 그대로 재사용한다. */
interface ApiDashboardSummary {
  counts: { matched: number; newToday: number; urgent: number; saved: number }
  matched: Parameters<typeof mapAnnouncement>[0][]
  urgent: Parameters<typeof mapAnnouncement>[0][]
  saved: Parameters<typeof mapAnnouncement>[0][]
}

export interface DashboardSummary {
  counts: ApiDashboardSummary['counts']
  matched: Announcement[]
  urgent: Announcement[]
  saved: Announcement[]
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get<ApiDashboardSummary>('/dashboard/summary')
  return {
    counts: data.counts,
    matched: data.matched.map(mapAnnouncement),
    urgent: data.urgent.map(mapAnnouncement),
    saved: data.saved.map(mapAnnouncement),
  }
}

/** back/app/api/v1/dashboard.py의 GET /dashboard/trend가 내려주는 필드.
 * series는 작년·올해 순으로 2개, counts는 1~12월 매칭 건수(길이 12). */
export interface DashboardTrend {
  months: string[]
  series: { year: number; counts: number[] }[]
}

export async function getDashboardTrend(): Promise<DashboardTrend> {
  const { data } = await api.get<DashboardTrend>('/dashboard/trend')
  return data
}
