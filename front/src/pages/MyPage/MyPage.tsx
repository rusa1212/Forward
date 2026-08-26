import { useLocation, useNavigate } from 'react-router-dom'
import ProfileTab from './ProfileTab'
import KeywordsTab from './KeywordsTab'
import AlertsTab from './AlertsTab'
import type { MyTab } from '@/types'

const TABS: [MyTab, string][] = [['profile', '내 정보'], ['keywords', '키워드 관리'], ['alerts', '알림 설정']]

const TAB_PATH: Record<MyTab, string> = {
  profile: '/mypage',
  keywords: '/mypage/keywords',
  alerts: '/mypage/alerts',
}

function tabFromPath(pathname: string): MyTab {
  if (pathname.startsWith('/mypage/keywords')) return 'keywords'
  if (pathname.startsWith('/mypage/alerts')) return 'alerts'
  return 'profile'
}

export default function MyPage() {
  const navigate = useNavigate()
  const { pathname, search } = useLocation()
  const tab = tabFromPath(pathname)

  // 상세 모달(?detail=)이 열린 채 탭을 옮겨도 모달 상태가 유지되도록 쿼리스트링을 그대로 넘긴다
  const goTab = (next: MyTab) => navigate(`${TAB_PATH[next]}${search}`)

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-xl font-bold text-gray-800 mb-6">마이페이지</h1>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-white rounded-xl p-1 shadow-sm border border-gray-100 w-fit">
        {TABS.map(([key, label]) => (
          <button key={key} onClick={() => goTab(key)} className={`px-5 py-2 rounded-lg text-sm font-semibold transition-colors ${tab === key ? 'bg-[#1d3557] text-white shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'profile' && <ProfileTab />}
      {tab === 'keywords' && <KeywordsTab />}
      {tab === 'alerts' && <AlertsTab onGoTab={goTab} />}
    </div>
  )
}
