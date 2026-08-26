import { Navigate, Route, Routes } from 'react-router-dom'
import RequireAuth from '@/components/RequireAuth'
import MainLayout from '@/components/layout/MainLayout'
import LoginPage from '@/pages/LoginPage'
import SignupPage from '@/pages/SignupPage'
import SignupDonePage from '@/pages/SignupDonePage'
import DashboardPage from '@/pages/DashboardPage/DashboardPage'
import SearchPage from '@/pages/SearchPage/SearchPage'
import MyPage from '@/pages/MyPage/MyPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/signup/done" element={<SignupDonePage />} />

      <Route element={<RequireAuth><MainLayout /></RequireAuth>}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/mypage" element={<MyPage />} />
        <Route path="/mypage/keywords" element={<MyPage />} />
        <Route path="/mypage/alerts" element={<MyPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
