import type { Keyword } from '@/types'

export const INITIAL_KEYWORDS: Keyword[] = [
  { id: 1, name: 'AI', matchCount: 12, dashboardAlert: true, emailAlert: true },
  { id: 2, name: '스마트시티', matchCount: 5, dashboardAlert: true, emailAlert: true },
  { id: 3, name: '플랫폼', matchCount: 8, dashboardAlert: true, emailAlert: false },
  { id: 4, name: '보안', matchCount: 3, dashboardAlert: true, emailAlert: true },
  { id: 5, name: '데이터', matchCount: 15, dashboardAlert: true, emailAlert: false },
]
