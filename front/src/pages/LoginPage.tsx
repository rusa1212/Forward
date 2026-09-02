import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '@/lib/auth'
import { api, ApiError } from '@/lib/api'

export default function LoginPage() {
  const navigate = useNavigate()
  const [empId, setEmpId] = useState('')
  const [pw, setPw] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onLogin = async () => {
    if (loading || !empId.trim() || !pw) return
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post<{ token: string; id: string; email: string; isAdmin: boolean }>(
        '/auth/login',
        { empId, pw }
      )
      login(data.token, data.isAdmin)
      navigate('/', { replace: true })
    } catch (e) {
      setError(e instanceof ApiError ? e.message : '로그인 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }
  const onGoSignup = () => navigate('/signup')

  return (
    <div className="min-h-screen bg-[#f0f2f5] flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg w-[380px] p-8">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 bg-[#1d3557] rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <span className="font-bold text-[#1d3557] text-lg tracking-tight">SMS Notice</span>
        </div>
        <h2 className="text-xl font-bold text-gray-800 mb-6">로그인</h2>
        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1.5 block">사번</label>
            <input value={empId} onChange={e => setEmpId(e.target.value)} className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition" placeholder="사번을 입력하세요" />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1.5 block">비밀번호</label>
            <input type="password" value={pw} onChange={e => setPw(e.target.value)} onKeyDown={e => e.key === 'Enter' && onLogin()} className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition" placeholder="비밀번호를 입력하세요" />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <button onClick={onLogin} disabled={loading} className="w-full bg-[#1d3557] text-white rounded-xl py-2.5 text-sm font-semibold hover:bg-[#16293f] transition-colors mt-1 disabled:opacity-50">
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </div>
        <p className="mt-5 text-center text-xs text-gray-400">
          계정이 없으신가요?{' '}
          <button onClick={onGoSignup} className="text-[#457b9d] font-semibold hover:underline">회원가입</button>
        </p>
      </div>
    </div>
  )
}
