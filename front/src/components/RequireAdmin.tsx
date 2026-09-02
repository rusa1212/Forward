import { Navigate } from 'react-router-dom'
import { isAdmin } from '@/lib/auth'

/** 관리자 전용 라우트 가드 — 관리자가 아니면 대시보드로 보낸다 (URL 직접 접근 차단). */
export default function RequireAdmin({ children }: { children: React.ReactNode }) {
  if (!isAdmin()) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}
