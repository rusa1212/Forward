import { api } from './api'
import type { Announcement, StatusType } from '@/types'

/** back/app/api/v1/announcements.py의 _serialize()가 실제로 내려주는 필드. */
interface ApiAnnouncement {
  id: string
  source: string
  external_id: string
  title: string
  department: string | null
  reception_start: string | null
  reception_end: string | null
  status: string | null
  statusLabel: StatusType | null
  detail_url: string | null
  summary: string | null
  collected_at: string
  dday: number | null
}

interface ListMeta {
  total: number
  page: number
  page_size: number
}

const SOURCE_LABELS: Record<string, string> = {
  kstartup: 'K-Startup',
  narajangteo: '나라장터',
  msit: '과기정통부',
}

/**
 * BE 응답을 FE `Announcement` 형태로 맞춘다. BE는 org/announcementType/field/postedDate/
 * receiptDate/deadlineTime/budget/contact/projectName/relatedKeywords 같은 필드를 아직
 * 내려주지 않으므로, 화면이 깨지지 않도록 있는 값(department/source/summary 등)으로 채우거나
 * 빈 값을 넣는다. (docs/fe/5th_wk_FE_연동작업.md 1절 참고)
 */
export function mapAnnouncement(raw: ApiAnnouncement): Announcement {
  const org = raw.department ?? '기관 정보 없음'
  const sourceLabel = SOURCE_LABELS[raw.source] ?? raw.source
  return {
    id: raw.id,
    title: raw.title,
    org,
    department: org,
    announcementType: sourceLabel,
    announceType: sourceLabel,
    field: '',
    status: raw.statusLabel ?? '접수중',
    postedDate: raw.reception_start ?? '-',
    receiptDate: raw.reception_start ?? '-',
    deadline: raw.reception_end ?? '기한 미정',
    deadlineTime: '-',
    dday: raw.dday,
    originalUrl: raw.detail_url ?? undefined,
    originalText: raw.summary ?? undefined,
    relatedKeywords: [],
  }
}

export interface AnnouncementQuery {
  q?: string
  /**
   * 키워드 매칭 모드 — 여러 개면 BE가 OR로 매칭한다(제목에 하나라도 포함되면 포함).
   * 대시보드 "매칭된 공고" 카운트·목록과 정확히 같은 집합을 만드는 용도.
   */
  keywords?: string[]
  statusLabel?: StatusType
  sort?: 'latest' | 'deadline' | 'title'
  page?: number
  pageSize?: number
}

export async function listAnnouncements(query: AnnouncementQuery) {
  const params = new URLSearchParams()
  if (query.q) params.set('q', query.q)
  for (const kw of query.keywords ?? []) params.append('keywords', kw)
  if (query.statusLabel) params.set('statusLabel', query.statusLabel)
  params.set('sort', query.sort ?? 'latest')
  params.set('page', String(query.page ?? 1))
  params.set('page_size', String(query.pageSize ?? 8))

  const { data, meta } = await api.get<ApiAnnouncement[]>(`/announcements?${params.toString()}`)
  return { items: data.map(mapAnnouncement), meta: meta as unknown as ListMeta }
}

export async function getAnnouncementDetail(id: string): Promise<Announcement> {
  const { data } = await api.get<ApiAnnouncement>(`/announcements/${id}`)
  return mapAnnouncement(data)
}
