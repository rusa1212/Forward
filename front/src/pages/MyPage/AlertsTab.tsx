import { useEffect, useState } from 'react'
import Toggle from '@/components/common/Toggle'
import { useAlertSettings } from '@/hooks/useAlertSettings'
import { useKeywordsContext } from '@/contexts/KeywordsContext'
import { useMe } from '@/hooks/useMe'
import { ApiError } from '@/lib/api'
import { sendMyNotificationEmail } from '@/lib/me'
import type { MyTab } from '@/types'

export default function AlertsTab({ onGoTab }: { onGoTab: (tab: MyTab) => void }) {
  const { keywords, toggleAlert, setAllEmailAlerts } = useKeywordsContext()
  const allKeywordEmailOn = keywords.length > 0 && keywords.every(k => k.emailAlert)
  const { settings, error: loadError, pending, save } = useAlertSettings()
  // 알림이 실제로 가는 주소를 보여주기 위해 조회 — 예전엔 'kim@company.kr'가 목업으로 박혀있어
  // 실제 로그인 계정과 다른 주소가 표시되는 버그가 있었다.
  const { me } = useMe()
  const [savedMsg, setSavedMsg] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [alertFreq, setAlertFreq] = useState<'daily' | 'weekly'>('daily')
  const [favDashboard, setFavDashboard] = useState(true)
  const [favEmail, setFavEmail] = useState(false)
  const [favDays, setFavDays] = useState<7 | 3 | 1>(7)
  const [sendingNow, setSendingNow] = useState(false)
  const [sendMsg, setSendMsg] = useState('')
  const [sendError, setSendError] = useState('')

  // 조회가 끝나면 폼 초기값을 서버 값으로 맞춘다
  useEffect(() => {
    if (!settings) return
    setAlertFreq(settings.emailFrequency)
    setFavDays(settings.deadlineAlertDays)
    setFavDashboard(settings.deadlineDashboardAlert)
    setFavEmail(settings.deadlineEmailAlert)
  }, [settings])

  const handleSave = async () => {
    setSaveError('')
    const message = await save({
      emailFrequency: alertFreq,
      deadlineAlertDays: favDays,
      deadlineDashboardAlert: favDashboard,
      deadlineEmailAlert: favEmail,
    })
    if (message) {
      setSaveError(message)
      return
    }
    setSavedMsg(true)
    setTimeout(() => setSavedMsg(false), 2000)
  }

  const handleSendNow = async () => {
    setSendingNow(true)
    setSendMsg('')
    setSendError('')
    try {
      const result = await sendMyNotificationEmail()
      setSendMsg(result.message)
      setTimeout(() => setSendMsg(''), 4000)
    } catch (e) {
      setSendError(e instanceof ApiError ? e.message : '이메일 발송에 실패했습니다.')
    } finally {
      setSendingNow(false)
    }
  }

  return (
    <div className="space-y-5 max-w-3xl">

      {/* 섹션 1 — 키워드 신규 공고 알림 */}
      <div className="bg-white rounded-xl border border-line overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-start gap-3">
          <div className="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg style={{width:18,height:18}} fill="none" viewBox="0 0 24 24" stroke="#101828" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-800">키워드 신규 공고 알림</h3>
            <p className="text-xs text-gray-400 mt-0.5">등록된 키워드에 매칭되는 신규 공고 발생 시 알림을 받습니다</p>
          </div>
        </div>
        {keywords.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">
            <p>등록된 키워드가 없습니다.</p>
            <button onClick={() => onGoTab('keywords')} className="mt-2 text-xs text-[#315cff] hover:underline">키워드 등록하러 가기</button>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50/80 border-b border-gray-100">
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 w-1/2">키워드</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">
                  <div className="flex items-center justify-center gap-1.5">
                    <svg style={{width:13,height:13}} fill="none" viewBox="0 0 24 24" stroke="#101828" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
                    대시보드 알림
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {keywords.map((kw, i) => (
                <tr key={kw.id} className={`hover:bg-gray-50/50 transition-colors ${i < keywords.length - 1 ? 'border-b border-gray-50' : ''}`}>
                  <td className="px-5 py-3.5">
                    <span className="bg-blue-50 text-blue-700 text-sm px-3 py-1 rounded-full border border-blue-100 font-semibold">{kw.name}</span>
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <Toggle enabled={kw.dashboardAlert} onChange={() => toggleAlert(kw.id, 'dashboard')} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="px-5 py-3 border-t border-gray-50 text-[11px] text-gray-400 leading-relaxed">
          이 키워드들의 매칭 공고를 이메일로도 받을지는 아래 <b className="text-gray-500 font-semibold">"이메일 발송"</b> 카드에서
          키워드 전체에 한 번에 설정합니다. 지금 쌓여 있는 알림을 당장 받고 싶다면 그 설정과 상관없이
          더 아래 <b className="text-gray-500 font-semibold">"지금 바로 받기"</b>를 누르세요.
        </p>
      </div>

      {/* 이메일 발송 — 토글(on/off) + 주기, 모든 키워드 공통 1개 */}
      <div className="bg-white rounded-xl border border-line overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-start gap-3">
          <div className="w-9 h-9 bg-green-50 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg style={{width:18,height:18}} fill="none" viewBox="0 0 24 24" stroke="#16a34a" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
          </div>
          <div className="flex-1 flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
                이메일 발송
                <span className="text-[9px] font-bold text-green-700 bg-green-100 px-1.5 py-0.5 rounded-full">자동</span>
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">
                {keywords.length === 0 ? '키워드를 먼저 등록하면 켤 수 있습니다' : '켜면 모든 키워드의 매칭 공고를 이메일로도 받습니다'}
              </p>
            </div>
            <Toggle
              enabled={allKeywordEmailOn}
              onChange={() => setAllEmailAlerts(!allKeywordEmailOn)}
            />
          </div>
        </div>
        <div className={`px-5 py-4 flex gap-2 transition-opacity ${allKeywordEmailOn ? '' : 'opacity-40 pointer-events-none'}`}>
          {([['daily', '매일 오전 9시'], ['weekly', '주 1회 (월요일)']] as const).map(([val, label]) => (
            <button key={val} onClick={() => setAlertFreq(val)}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold border transition-colors ${alertFreq === val ? 'bg-[#101828] text-white border-[#101828]' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* 지금 바로 받기 — 위 자동 발송 설정과 별개로, 지금 쌓인 알림을 즉시 1회 발송 */}
      <div className="bg-violet-50/40 rounded-xl border border-violet-200 overflow-hidden">
        <div className="px-5 py-4 flex items-start gap-3">
          <div className="w-9 h-9 bg-violet-100 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg style={{width:18,height:18}} fill="none" viewBox="0 0 24 24" stroke="#7c3aed" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
              지금 바로 받기
              <span className="text-[9px] font-bold text-violet-700 bg-violet-100 px-1.5 py-0.5 rounded-full">즉시 · 1회성</span>
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              위 토글·발송 주기 설정과 <b className="font-semibold">무관하게</b>, 아직 이메일로 안 보낸 알림을 지금 이 순간 한 번 보냅니다.
              설정을 바꾸지 않고 지금 밀린 알림만 확인하고 싶을 때 누르세요.
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2">
              <button
                onClick={handleSendNow}
                disabled={sendingNow}
                className="bg-violet-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-violet-700 disabled:opacity-50 transition-colors"
              >
                {sendingNow ? '보내는 중...' : '지금 이메일로 받기'}
              </button>
              {sendMsg && (
                <span className="text-sm text-green-600 font-medium flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  {sendMsg}
                </span>
              )}
              {sendError && <span className="text-sm text-red-600 font-medium">{sendError}</span>}
            </div>
          </div>
        </div>
      </div>

      {/* 섹션 2 — 즐겨찾기 마감 임박 알림 */}
      <div className="bg-white rounded-xl border border-line overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-start gap-3">
          <div className="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg style={{width:18,height:18}} fill="none" viewBox="0 0 24 24" stroke="#d97706" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-800">즐겨찾기 마감 임박 알림</h3>
            <p className="text-xs text-gray-400 mt-0.5">즐겨찾기한 공고의 마감일이 다가오면 알림을 받습니다</p>
          </div>
        </div>
        <div className="px-5 py-5 space-y-5">
          {/* D-day 기준 */}
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-2.5">마감 임박 기준일</p>
            <div className="flex gap-2">
              {([7, 3, 1] as const).map(d => (
                <button key={d} onClick={() => setFavDays(d)}
                  className={`px-5 py-2 rounded-xl text-sm font-semibold border transition-colors ${favDays === d ? 'bg-amber-500 text-white border-amber-500' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}>
                  D-{d}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">마감 {favDays}일 전부터 알림을 발송합니다</p>
          </div>
          {/* 알림 채널 */}
          <div className="border-t border-gray-50 pt-4 space-y-3">
            <p className="text-xs font-semibold text-gray-500">알림 채널</p>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <svg style={{width:16,height:16}} fill="none" viewBox="0 0 24 24" stroke="#101828" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
                <span className="text-sm text-gray-700">대시보드 알림</span>
              </div>
              <Toggle enabled={favDashboard} onChange={() => setFavDashboard(v => !v)} />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <svg style={{width:16,height:16}} fill="none" viewBox="0 0 24 24" stroke="#16a34a" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                <div>
                  <span className="text-sm text-gray-700">이메일 발송</span>
                  <span className="ml-1.5 text-[9px] font-bold text-green-700 bg-green-100 px-1.5 py-0.5 rounded-full align-middle">자동</span>
                  <span className="ml-2 text-xs text-[#315cff]">{me?.email ?? '불러오는 중...'}</span>
                  <button onClick={() => onGoTab('profile')} className="ml-1.5 text-[10px] text-gray-300 hover:text-gray-500 underline transition-colors">변경</button>
                </div>
              </div>
              <Toggle enabled={favEmail} onChange={() => setFavEmail(v => !v)} />
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={pending}
          className="bg-[#101828] text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-[#1F3FAF] disabled:opacity-50 transition-colors"
        >
          {pending ? '저장 중...' : '저장'}
        </button>
        {savedMsg && (
          <span className="text-sm text-green-600 font-medium flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            저장되었습니다.
          </span>
        )}
        {(saveError || loadError) && (
          <span className="text-sm text-red-600 font-medium">{saveError || loadError}</span>
        )}
      </div>
    </div>
  )
}
