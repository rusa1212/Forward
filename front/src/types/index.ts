export type Page = 'login' | 'signup' | 'signupDone' | 'dashboard' | 'search' | 'mypage' | 'mypage-keywords'
export type MyTab = 'profile' | 'keywords' | 'alerts'
export type StatusType = '접수중' | '접수예정' | '마감임박' | '마감'

export interface Announcement {
  id: number
  title: string
  org: string
  department: string
  announcementType: string
  announceType: string
  field: string
  status: StatusType
  postedDate: string
  receiptDate: string
  deadline: string
  deadlineTime: string
  dday: number
  budget?: string
  contact?: string
  projectName?: string
  originalUrl?: string
  originalText?: string
  relatedKeywords: string[]
  isFavorite?: boolean
}

export interface Keyword {
  id: number
  name: string
  matchCount: number
  dashboardAlert: boolean
  emailAlert: boolean
}
