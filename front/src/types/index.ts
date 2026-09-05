export type Page = 'login' | 'signup' | 'signupDone' | 'dashboard' | 'search' | 'mypage' | 'mypage-keywords'
export type MyTab = 'profile' | 'keywords' | 'alerts'
export type StatusType = '접수중' | '접수예정' | '마감임박' | '마감'
export type SortType = 'latest' | 'deadline' | 'title'

export interface Announcement {
  id: string
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
  /** BE가 접수시작/종료일 정보를 못 내려주는 공고(예: msit)는 null */
  dday: number | null
  budget?: string
  contact?: string
  projectName?: string
  originalUrl?: string
  originalText?: string
  relatedKeywords: string[]
  isFavorite?: boolean
}

export interface Keyword {
  id: string
  name: string
  matchCount: number
  dashboardAlert: boolean
  emailAlert: boolean
}

export interface AdminEmployee {
  empId: string
  name: string
  department: string | null
  createdAt: string
  joined: boolean
}

export interface AdminUser {
  id: string
  empId: string
  name: string
  department: string | null
  email: string
  isAdmin: boolean
  createdAt: string
}

/** back/app/api/v1/me.py의 _serialize_me()가 내려주는 필드 그대로. */
export interface Me {
  id: string
  /** 사번 — 로그인 식별자라 변경 불가 */
  empId: string
  /** employees 테이블 소유라 읽기 전용. 명부에 없으면 null */
  name: string | null
  department: string | null
  /** 사용자가 고칠 수 있는 유일한 필드 */
  email: string
}

/**
 * back/app/api/v1/notifications.py의 _serialize()가 내려주는 필드 그대로.
 * DOM 전역 `Notification`과 이름이 겹치지 않도록 App 접두어를 붙였다.
 */
export interface AppNotification {
  id: string
  /** "신규매칭" | "마감임박" */
  notifyType: string
  title: string
  /** 매칭된 키워드. 마감임박처럼 키워드와 무관한 건은 null */
  keyword: string | null
  /** 클릭 시 열 공고. 공고가 지워졌으면 null */
  announcementId: string | null
  isRead: boolean
  /** UTC인데 타임존 표기가 없다 — lib/datetime.ts의 parseServerDate를 거쳐야 한다 */
  createdAt: string
}
