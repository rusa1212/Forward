import { useEffect, useState } from 'react'
import { useMe } from '@/hooks/useMe'
import { MIN_PASSWORD_LENGTH } from '@/lib/me'

/** 값이 비어 있을 때 표에 표시할 문구 */
const EMPTY = '-'

export default function ProfileTab() {
  const { me, loading, error, pending, refresh, saveEmail, savePassword } = useMe()

  /** view | email(이메일 수정) | password(비밀번호 변경) — 한 번에 하나만 연다 */
  const [mode, setMode] = useState<'view' | 'email' | 'password'>('view')
  const [formError, setFormError] = useState('')
  const [doneMsg, setDoneMsg] = useState('')

  const [emailInput, setEmailInput] = useState('')
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')

  // 조회가 끝나거나 갱신되면 수정 폼의 초기값을 서버 값으로 맞춘다
  useEffect(() => {
    if (me) setEmailInput(me.email)
  }, [me])

  const closeForm = () => {
    setMode('view')
    setFormError('')
    setCurrentPw('')
    setNewPw('')
    setConfirmPw('')
    if (me) setEmailInput(me.email)
  }

  const openForm = (next: 'email' | 'password') => {
    closeForm()
    setDoneMsg('')
    setMode(next)
  }

  const showDone = (message: string) => {
    setDoneMsg(message)
    window.setTimeout(() => setDoneMsg(''), 3000)
  }

  const handleSaveEmail = async () => {
    const failure = await saveEmail(emailInput)
    if (failure) {
      setFormError(failure)
      return
    }
    closeForm()
    showDone('이메일이 변경되었습니다.')
  }

  const handleSavePassword = async () => {
    const failure = await savePassword(currentPw, newPw, confirmPw, MIN_PASSWORD_LENGTH)
    if (failure) {
      setFormError(failure)
      return
    }
    closeForm()
    showDone('비밀번호가 변경되었습니다.')
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 max-w-lg text-sm text-gray-400">
        내 정보를 불러오는 중입니다...
      </div>
    )
  }

  if (error || !me) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 max-w-lg">
        <p className="text-sm text-red-600">{error || '내 정보를 불러오지 못했습니다.'}</p>
        <button onClick={refresh} className="mt-3 border border-gray-200 text-gray-600 px-4 py-2 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors">
          다시 시도
        </button>
      </div>
    )
  }

  const displayName = me.name ?? me.empId
  const rows: [string, string][] = [
    ['이름', me.name ?? EMPTY],
    ['부서', me.department ?? EMPTY],
    ['사번', me.empId],
    ['이메일', me.email],
  ]

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 max-w-lg">
      <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-100">
        <div className="w-14 h-14 bg-[#1d3557] rounded-2xl flex items-center justify-center text-white text-xl font-bold shadow-md">
          {displayName.slice(0, 1)}
        </div>
        <div>
          <h3 className="font-bold text-gray-800">{displayName}</h3>
          <p className="text-sm text-gray-400">{me.email}</p>
        </div>
      </div>

      <div className="space-y-4">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-center py-2 border-b border-gray-50 last:border-0">
            <span className="text-xs text-gray-400 font-medium w-20 flex-shrink-0">{label}</span>
            <span className="text-sm text-gray-800 font-medium">{value}</span>
          </div>
        ))}
      </div>

      <p className="mt-4 text-[11px] text-gray-400">
        이름·부서·사번은 사원 명부에서 가져오는 값이라 직접 수정할 수 없습니다. 변경이 필요하면 관리자에게 문의해주세요.
      </p>

      {mode === 'view' && (
        <div className="mt-6 flex items-center gap-3">
          <button onClick={() => openForm('email')} className="bg-[#1d3557] text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-[#16293f] transition-colors">
            정보 수정
          </button>
          <button onClick={() => openForm('password')} className="border border-gray-200 text-gray-600 px-5 py-2 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors">
            비밀번호 변경
          </button>
          {doneMsg && (
            <span className="text-sm text-green-600 font-medium flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              {doneMsg}
            </span>
          )}
        </div>
      )}

      {mode === 'email' && (
        <form
          className="mt-6 pt-5 border-t border-gray-100 space-y-3"
          onSubmit={e => { e.preventDefault(); handleSaveEmail() }}
        >
          <h4 className="text-sm font-semibold text-gray-800">정보 수정</h4>
          <label className="block">
            <span className="text-xs text-gray-400 font-medium">이메일</span>
            <input
              type="email"
              value={emailInput}
              onChange={e => setEmailInput(e.target.value)}
              autoFocus
              className="mt-1 w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#457b9d]"
            />
          </label>
          {formError && <p className="text-xs text-red-600">{formError}</p>}
          <div className="flex gap-2 pt-1">
            <button type="submit" disabled={pending} className="bg-[#1d3557] text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-[#16293f] transition-colors disabled:opacity-50">
              {pending ? '저장 중...' : '저장'}
            </button>
            <button type="button" onClick={closeForm} className="border border-gray-200 text-gray-600 px-5 py-2 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors">
              취소
            </button>
          </div>
        </form>
      )}

      {mode === 'password' && (
        <form
          className="mt-6 pt-5 border-t border-gray-100 space-y-3"
          onSubmit={e => { e.preventDefault(); handleSavePassword() }}
        >
          <h4 className="text-sm font-semibold text-gray-800">비밀번호 변경</h4>
          {([
            ['현재 비밀번호', currentPw, setCurrentPw, 'current-password'],
            ['새 비밀번호', newPw, setNewPw, 'new-password'],
            ['새 비밀번호 확인', confirmPw, setConfirmPw, 'new-password'],
          ] as const).map(([label, value, setValue, autoComplete], i) => (
            <label key={label} className="block">
              <span className="text-xs text-gray-400 font-medium">{label}</span>
              <input
                type="password"
                value={value}
                onChange={e => setValue(e.target.value)}
                autoComplete={autoComplete}
                autoFocus={i === 0}
                className="mt-1 w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#457b9d]"
              />
            </label>
          ))}
          <p className="text-[11px] text-gray-400">새 비밀번호는 {MIN_PASSWORD_LENGTH}자 이상이어야 합니다.</p>
          {formError && <p className="text-xs text-red-600">{formError}</p>}
          <div className="flex gap-2 pt-1">
            <button type="submit" disabled={pending} className="bg-[#1d3557] text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-[#16293f] transition-colors disabled:opacity-50">
              {pending ? '변경 중...' : '변경'}
            </button>
            <button type="button" onClick={closeForm} className="border border-gray-200 text-gray-600 px-5 py-2 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors">
              취소
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
