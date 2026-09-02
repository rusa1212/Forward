import { Navigate } from 'react-router-dom'
import { isAdmin } from '@/lib/auth'

/** 일반 사용자 전용 라우트 가드 — 관리자 계정은 대시보드/검색 등 대신 관리자 페이지로 보낸다. */
export default function RequireNonAdmin({ children }: { children: React.ReactNode }) {
  if (isAdmin()) {
    return <Navigate to="/admin" replace />
  }
  return <>{children}</>
}
