import { useState } from 'react'
import Toggle from '@/components/common/Toggle'
import { useKeywordsContext } from '@/contexts/KeywordsContext'
import type { MyTab } from '@/types'

export default function AlertsTab({ onGoTab }: { onGoTab: (tab: MyTab) => void }) {
  const { keywords, toggleAlert } = useKeywordsContext()
  const [savedMsg, setSavedMsg] = useState(false)
  const [alertFreq, setAlertFreq] = useState<'daily' | 'weekly'>('daily')
  const [favDashboard, setFavDashboard] = useState(true)
  const [favEmail, setFavEmail] = useState(false)
  const [favDays, setFavDays] = useState<7 | 3 | 1>(7)

  const handleSave = () => {
    setSavedMsg(true)
    setTimeout(() => setSavedMsg(false), 2000)
  }

  return (
    <div className="space-y-5 max-w-3xl">

      {/* 섹션 1 — 키워드 신규 공고 알림 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-start gap-3">
          <div className="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg style={{width:18,height:18}} fill="none" viewBox="0 0 24 24" stroke="#1d3557" strokeWidth={2}>
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
            <button onClick={() => onGoTab('keywords')} className="mt-2 text-xs text-[#457b9d] hover:underline">키워드 등록하러 가기</button>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50/80 border-b border-gray-100">
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 w-1/2">키워드</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">
                  <div className="flex items-center justify-center gap-1.5">
                    <svg style={{width:13,height:13}} fill="none" viewBox="0 0 24 24" stroke="#1d3557" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
                    대시보드 알림
                  </div>
                </th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500">
                  <div className="flex items-center justify-center gap-1.5">
                    <svg style={{width:13,height:13}} fill="none" viewBox="0 0 24 24" stroke="#16a34a" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                    이메일 발송
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
                  <td className="px-4 py-3.5 text-center">
                    <Toggle enabled={kw.emailAlert} onChange={() => toggleAlert(kw.id, 'email')} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* 이메일 발송 시간 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-start gap-3">
          <div className="w-9 h-9 bg-green-50 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg style={{width:18,height:18}} fill="none" viewBox="0 0 24 24" stroke="#16a34a" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-800">이메일 발송 시간</h3>
            <p className="text-xs text-gray-400 mt-0.5">이메일 알림을 얼마나 자주 받을지 설정합니다</p>
          </div>
        </div>
        <div className="px-5 py-4 flex gap-2">
          {([['daily', '매일 오전 9시'], ['weekly', '주 1회 (월요일)']] as const).map(([val, label]) => (
            <button key={val} onClick={() => setAlertFreq(val)}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold border transition-colors ${alertFreq === val ? 'bg-[#1d3557] text-white border-[#1d3557]' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* 섹션 2 — 즐겨찾기 마감 임박 알림 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
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
                <svg style={{width:16,height:16}} fill="none" viewBox="0 0 24 24" stroke="#1d3557" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
                <span className="text-sm text-gray-700">대시보드 알림</span>
              </div>
              <Toggle enabled={favDashboard} onChange={() => setFavDashboard(v => !v)} />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <svg style={{width:16,height:16}} fill="none" viewBox="0 0 24 24" stroke="#16a34a" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                <div>
                  <span className="text-sm text-gray-700">이메일 발송</span>
                  <span className="ml-2 text-xs text-[#457b9d]">kim@company.kr</span>
                  <button onClick={() => onGoTab('profile')} className="ml-1.5 text-[10px] text-gray-300 hover:text-gray-500 underline transition-colors">변경</button>
                </div>
              </div>
              <Toggle enabled={favEmail} onChange={() => setFavEmail(v => !v)} />
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button onClick={handleSave} className="bg-[#1d3557] text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-[#16293f] transition-colors">
          저장
        </button>
        {savedMsg && (
          <span className="text-sm text-green-600 font-medium flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            저장되었습니다.
          </span>
        )}
      </div>
    </div>
  )
}
