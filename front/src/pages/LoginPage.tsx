import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Eye, EyeOff, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { login } from '@/lib/auth'
import { api, ApiError } from '@/lib/api'
import iconGradient from '@/assets/brand/forward-icon-gradient.png'

export default function LoginPage() {
  const navigate = useNavigate()
  const [empId, setEmpId] = useState('')
  const [pw, setPw] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onLogin = async () => {
    if (loading || !empId.trim() || !pw) return
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post<{ token: string; id: string; email: string; name: string; isAdmin: boolean }>(
        '/auth/login',
        { empId, pw }
      )
      login(data.token, data.isAdmin, data.name)
      // 로그인 후에도 홈(랜딩)에서 시작 — 상단 GNB로 대시보드/검색/마이페이지 이동
      navigate(data.isAdmin ? '/admin' : '/', { replace: true })
    } catch (e) {
      setError(e instanceof ApiError ? e.message : '로그인 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-canvas flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-[400px] flex flex-col items-center rise rise-1">
        <img src={iconGradient} alt="Forward" className="w-16 h-16" />
        <h1 className="mt-4 text-2xl font-bold text-strong tracking-[-0.3px]">Forward R&D Monitor</h1>
        <p className="mt-1.5 text-sm text-body">공공 R&D 공고, 키워드로 한 번에 모아보세요.</p>

        <div className="rise rise-2 mt-8 w-full bg-surface border border-line rounded-xl p-7">
          {error && (
            <div className="mb-5 px-3.5 py-3 rounded-[10px] bg-[rgba(240,68,56,0.08)] flex items-center gap-2 animate-in fade-in-0 slide-in-from-top-1">
              <AlertTriangle className="h-4 w-4 text-danger shrink-0" strokeWidth={2} />
              <span className="text-danger text-[13px]">{error}</span>
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="login-empid" className="block text-[13px] font-semibold text-strong">사번</label>
              <input
                id="login-empid"
                value={empId}
                onChange={e => setEmpId(e.target.value)}
                placeholder="사번을 입력하세요"
                className="w-full h-[46px] px-3.5 bg-[#f2f4f7] rounded-xl text-sm text-strong placeholder:text-muted2 focus:outline-none focus:bg-white focus:ring-2 focus:ring-primary2/30 focus:border-primary2 border border-transparent transition-all"
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="login-pw" className="block text-[13px] font-semibold text-strong">비밀번호</label>
              <div className="relative">
                <input
                  id="login-pw"
                  type={showPw ? 'text' : 'password'}
                  value={pw}
                  onChange={e => setPw(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && onLogin()}
                  placeholder="비밀번호를 입력하세요"
                  className="w-full h-[46px] pl-3.5 pr-11 bg-[#f2f4f7] rounded-xl text-sm text-strong placeholder:text-muted2 focus:outline-none focus:bg-white focus:ring-2 focus:ring-primary2/30 focus:border-primary2 border border-transparent transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  aria-label={showPw ? '비밀번호 숨기기' : '비밀번호 표시'}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted2 hover:text-body transition-colors"
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button
              onClick={onLogin}
              disabled={loading || !empId.trim() || !pw}
              className={cn(
                'pressable w-full h-12 mt-1 rounded-[10px] bg-primary2 hover:bg-primary-hover active:bg-primary-pressed',
                'text-white text-[15px] font-bold flex items-center justify-center gap-2 transition-colors',
                'disabled:opacity-40 disabled:hover:bg-primary2'
              )}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  로그인 중...
                </>
              ) : (
                '로그인'
              )}
            </button>
          </div>

          <p className="mt-5 text-center text-[13px] text-body">
            계정이 없으신가요?{' '}
            <button type="button" onClick={() => navigate('/signup')} className="text-primary2 font-semibold hover:text-primary-hover transition-colors">
              회원가입
            </button>
          </p>
        </div>

        <button onClick={() => navigate('/welcome')} className="rise rise-3 mt-6 text-xs text-sub hover:text-strong transition-colors">
          서비스 소개 보기 ›
        </button>
      </div>
    </div>
  )
}
