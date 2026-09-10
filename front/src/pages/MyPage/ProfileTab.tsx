import { useNavigate } from 'react-router-dom'
import { Bell, Bookmark, ChevronRight, Tag } from 'lucide-react'
import { getName } from '@/lib/auth'
import { useKeywordsContext } from '@/contexts/KeywordsContext'
import { useFavoritesContext } from '@/contexts/FavoritesContext'
import type { MyTab } from '@/types'

export default function ProfileTab({ onGoTab }: { onGoTab: (tab: MyTab) => void }) {
  const navigate = useNavigate()
  const { keywords } = useKeywordsContext()
  const { favorites } = useFavoritesContext()
  const name = getName() || '사용자'
  const dashboardOn = keywords.filter(k => k.dashboardAlert).length
  const emailOn = keywords.filter(k => k.emailAlert).length

  const usage = [
    { icon: Tag, label: '등록 키워드', value: `${keywords.length}개`, onClick: () => onGoTab('keywords') },
    { icon: Bookmark, label: '저장 공고', value: `${favorites.size}건`, onClick: () => navigate('/search') },
    { icon: Bell, label: '알림 설정', value: `${dashboardOn + emailOn > 0 ? '사용 중' : '꺼짐'}`, onClick: () => onGoTab('alerts') },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_minmax(0,1fr)] gap-5 items-start">
      {/* 프로필 카드 */}
      <div className="bg-surface border border-line rounded-xl px-7 py-6">
        <div className="flex items-center gap-4 pb-5 border-b border-line">
          <div className="w-12 h-12 rounded-full bg-soft text-primary2 text-lg font-bold flex items-center justify-center">
            {name.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-strong">{name}</h3>
              <span className="px-2 py-0.5 rounded-full bg-[#f2f4f7] text-sub text-[11px] font-semibold whitespace-nowrap">일반 계정</span>
            </div>
            <p className="mt-0.5 text-[13px] text-muted2">kim@company.kr</p>
          </div>
        </div>

        <div className="py-2">
          {[
            { label: '이름', value: name, roster: true },
            { label: '사번', value: '20230001', roster: true },
            { label: '부서', value: '연구기획팀', roster: true },
            { label: '아이디', value: 'kim_manager' },
          ].map(item => (
            <div key={item.label} className="flex items-center py-3 border-b border-line last:border-0">
              <span className="w-20 shrink-0 text-xs font-medium text-muted2">{item.label}</span>
              <span className="text-sm font-medium text-strong">{item.value}</span>
              {item.roster && (
                <span className="ml-2 px-1.5 py-0.5 rounded bg-[#f2f4f7] text-muted2 text-[10px] font-medium whitespace-nowrap">명부 기준</span>
              )}
            </div>
          ))}
        </div>

        <div className="pt-3 space-y-2">
          <label className="block text-xs font-medium text-muted2">이메일</label>
          <div className="flex items-center gap-2">
            <input
              defaultValue="kim@company.kr"
              className="flex-1 h-[42px] px-3.5 bg-white border border-line rounded-[10px] text-sm text-strong focus:outline-none focus:border-primary2 focus:ring-2 focus:ring-primary2/20 transition-all"
            />
            <button className="pressable h-[42px] px-5 rounded-[10px] bg-primary2 hover:bg-primary-hover text-white text-sm font-semibold transition-colors shrink-0">
              저장
            </button>
          </div>
          <p className="text-[11px] text-muted2">키워드 매칭 알림이 이 주소로 발송됩니다.</p>
        </div>
      </div>

      {/* 우측 모듈 */}
      <div className="space-y-5">
        <div className="bg-surface border border-line rounded-xl px-7 py-5">
          <h3 className="text-[15px] font-bold text-strong">이용 현황</h3>
          <div className="mt-2">
            {usage.map(({ icon: Icon, label, value, onClick }) => (
              <button
                key={label}
                onClick={onClick}
                className="w-full flex items-center justify-between py-3 border-b border-line last:border-0 text-left hover:bg-subtle -mx-2 px-2 rounded-lg transition-colors"
              >
                <span className="flex items-center gap-2.5">
                  <Icon className="w-4 h-4 text-primary2" strokeWidth={1.8} />
                  <span className="text-sm text-body">{label}</span>
                </span>
                <span className="flex items-center gap-1 text-sm font-semibold text-strong whitespace-nowrap">
                  {value}
                  <ChevronRight className="w-3.5 h-3.5 text-faint" strokeWidth={2} />
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-surface border border-line rounded-xl px-7 py-5">
          <div className="flex items-center justify-between">
            <h3 className="text-[15px] font-bold text-strong">알림 요약</h3>
            <button onClick={() => onGoTab('alerts')} className="text-xs font-medium text-primary2 hover:text-primary-hover">변경 ›</button>
          </div>
          <ul className="mt-3 space-y-2 text-[13px] text-body">
            <li className="flex justify-between">
              <span>대시보드 알림 키워드</span>
              <span className="font-semibold text-strong tabular-nums whitespace-nowrap">{dashboardOn}개</span>
            </li>
            <li className="flex justify-between">
              <span>이메일 알림 키워드</span>
              <span className="font-semibold text-strong tabular-nums whitespace-nowrap">{emailOn}개</span>
            </li>
            <li className="flex justify-between">
              <span>발송 시간</span>
              <span className="font-semibold text-strong whitespace-nowrap">매일 09:00</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
