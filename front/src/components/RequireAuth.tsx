import { Navigate, useLocation } from 'react-router-dom'
import { isAuthenticated } from '@/lib/auth'

/** 데모 수준의 인증 가드 — 로그인하지 않았으면 로그인 화면으로 보낸다. */
export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}
