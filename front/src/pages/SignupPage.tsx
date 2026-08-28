import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/lib/api'

export default function SignupPage() {
  const navigate = useNavigate()
  const onDone = () => navigate('/signup/done', { replace: true })
  const onGoLogin = () => navigate('/login')

  const [empId, setEmpId] = useState('')
  const [name, setName] = useState('')
  const [verifyState, setVerifyState] = useState<'idle' | 'loading' | 'ok' | 'fail'>('idle')
  const [pw, setPw] = useState('')
  const [pwConfirm, setPwConfirm] = useState('')
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [signupError, setSignupError] = useState('')

  const verified = verifyState === 'ok'
  const pwMismatch = pwConfirm.length > 0 && pw !== pwConfirm

  const handleVerify = async () => {
    if (!empId.trim() || !name.trim()) return
    setVerifyState('loading')
    try {
      const { data } = await api.post<{ verified: boolean }>('/auth/verify-employee', { empId, name })
      setVerifyState(data.verified ? 'ok' : 'fail')
    } catch {
      setVerifyState('fail')
    }
  }

  const canSubmit = verified && pw.length >= 6 && pw === pwConfirm && email.includes('@')

  const handleSubmit = async () => {
    if (!canSubmit || submitting) return
    setSubmitting(true)
    setSignupError('')
    try {
      await api.post('/auth/signup', { empId, name, email, pw })
      onDone()
    } catch (e) {
      setSignupError(e instanceof ApiError ? e.message : '회원가입 중 오류가 발생했습니다.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f0f2f5] flex items-center justify-center py-10">
      <div className="bg-white rounded-2xl shadow-lg w-[420px] p-8">
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 bg-[#1d3557] rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <span className="font-bold text-[#1d3557] text-lg tracking-tight">SMS Notice</span>
        </div>
        <h2 className="text-xl font-bold text-gray-800 mb-1">회원가입</h2>
        <p className="text-xs text-gray-400 mb-6">사번과 이름으로 계정을 만들 수 있습니다</p>

        <div className="space-y-4">
          {/* 사번 + 이름 인증 박스 */}
          <div className={`rounded-xl border-2 p-4 space-y-3 transition-colors ${verified ? 'border-green-200 bg-green-50/40' : 'border-gray-100 bg-gray-50/60'}`}>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs font-semibold text-gray-600">사원 정보 인증</p>
              {verified && (
                <span className="flex items-center gap-1 text-xs font-semibold text-green-600">
                  <svg style={{width:13,height:13}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/></svg>
                  인증 완료
                </span>
              )}
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 mb-1.5 block">사번</label>
              <input
                value={empId} onChange={e => { setEmpId(e.target.value); setVerifyState('idle') }}
                disabled={verified}
                className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition disabled:bg-gray-100 disabled:text-gray-400"
                placeholder="사번을 입력하세요"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 mb-1.5 block">이름</label>
              <input
                value={name} onChange={e => { setName(e.target.value); setVerifyState('idle') }}
                disabled={verified}
                className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition disabled:bg-gray-100 disabled:text-gray-400"
                placeholder="이름을 입력하세요"
              />
            </div>
            {verifyState === 'fail' && (
              <p className="text-xs text-red-500 flex items-center gap-1">
                <svg style={{width:12,height:12}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                사번 또는 이름이 일치하지 않습니다. 다시 확인해주세요.
              </p>
            )}
            {!verified && (
              <button
                onClick={handleVerify}
                disabled={!empId.trim() || !name.trim() || verifyState === 'loading'}
                className="w-full border border-[#1d3557] text-[#1d3557] rounded-xl py-2.5 text-sm font-semibold hover:bg-[#1d3557] hover:text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {verifyState === 'loading' ? (
                  <>
                    <svg className="animate-spin" style={{width:14,height:14}} fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg>
                    인증 중...
                  </>
                ) : '사원 정보 인증하기'}
              </button>
            )}
            {verified && (
              <button onClick={() => { setVerifyState('idle'); setEmpId(''); setName('') }} className="w-full text-xs text-gray-400 hover:text-gray-600 transition-colors">
                다시 입력하기
              </button>
            )}
          </div>

          {/* 비밀번호 */}
          <div className={`transition-opacity ${verified ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
            <div className="space-y-3.5">
              <div>
                <label className="text-xs font-medium text-gray-500 mb-1.5 block">비밀번호</label>
                <input type="password" value={pw} onChange={e => setPw(e.target.value)} disabled={!verified}
                  className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition"
                  placeholder="6자 이상 입력하세요" />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 mb-1.5 block">비밀번호 확인</label>
                <input type="password" value={pwConfirm} onChange={e => setPwConfirm(e.target.value)} disabled={!verified}
                  className={`w-full border rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 transition ${pwMismatch ? 'border-red-300 focus:border-red-400 focus:ring-red-200/30' : 'border-gray-200 focus:border-[#457b9d] focus:ring-[#457b9d]/20'}`}
                  placeholder="비밀번호를 다시 입력하세요" />
                {pwMismatch && <p className="text-xs text-red-500 mt-1">비밀번호가 일치하지 않습니다</p>}
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 mb-1.5 block">이메일</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} disabled={!verified}
                  className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition"
                  placeholder="알림 수신 이메일 주소" />
              </div>
            </div>
          </div>

          {signupError && <p className="text-xs text-red-500">{signupError}</p>}
          <button onClick={handleSubmit} disabled={!canSubmit || submitting}
            className="w-full bg-[#1d3557] text-white rounded-xl py-2.5 text-sm font-semibold hover:bg-[#16293f] transition-colors disabled:opacity-40 disabled:cursor-not-allowed mt-1">
            {submitting ? '가입 처리 중...' : '회원가입'}
          </button>
        </div>

        <p className="mt-5 text-center text-xs text-gray-400">
          이미 계정이 있으신가요?{' '}
          <button onClick={onGoLogin} className="text-[#457b9d] font-semibold hover:underline">로그인</button>
        </p>
      </div>
    </div>
  )
}
