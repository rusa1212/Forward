import { Navigate, Route, Routes } from 'react-router-dom'
import RequireAuth from '@/components/RequireAuth'
import RequireAdmin from '@/components/RequireAdmin'
import RequireNonAdmin from '@/components/RequireNonAdmin'
import MainLayout from '@/components/layout/MainLayout'
import LandingPage from '@/pages/LandingPage'
import LoginPage from '@/pages/LoginPage'
import SignupPage from '@/pages/SignupPage'
import SignupDonePage from '@/pages/SignupDonePage'
import DashboardPage from '@/pages/DashboardPage/DashboardPage'
import SearchPage from '@/pages/SearchPage/SearchPage'
import MyPage from '@/pages/MyPage/MyPage'
import AdminPage from '@/pages/AdminPage/AdminPage'

export default function App() {
  return (
    <Routes>
      {/* 홈(랜딩)이 첫 화면 — 로그인 전후 모두 '/'에서 시작한다 */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/welcome" element={<Navigate to="/" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/signup/done" element={<SignupDonePage />} />

      <Route element={<RequireAuth><MainLayout /></RequireAuth>}>
        <Route path="/dashboard" element={<RequireNonAdmin><DashboardPage /></RequireNonAdmin>} />
        <Route path="/search" element={<RequireNonAdmin><SearchPage /></RequireNonAdmin>} />
        <Route path="/mypage" element={<RequireNonAdmin><MyPage /></RequireNonAdmin>} />
        <Route path="/mypage/keywords" element={<RequireNonAdmin><MyPage /></RequireNonAdmin>} />
        <Route path="/mypage/alerts" element={<RequireNonAdmin><MyPage /></RequireNonAdmin>} />
        <Route path="/admin" element={<RequireAdmin><AdminPage /></RequireAdmin>} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
