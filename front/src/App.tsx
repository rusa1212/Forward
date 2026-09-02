import { Navigate, Route, Routes } from 'react-router-dom'
import RequireAuth from '@/components/RequireAuth'
import RequireAdmin from '@/components/RequireAdmin'
import RequireNonAdmin from '@/components/RequireNonAdmin'
import MainLayout from '@/components/layout/MainLayout'
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
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/signup/done" element={<SignupDonePage />} />

      <Route element={<RequireAuth><MainLayout /></RequireAuth>}>
        <Route path="/" element={<RequireNonAdmin><DashboardPage /></RequireNonAdmin>} />
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
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
