import { useLocation, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import ProfileTab from './ProfileTab'
import KeywordsTab from './KeywordsTab'
import AlertsTab from './AlertsTab'
import type { MyTab } from '@/types'

const TABS: [MyTab, string][] = [
  ['profile', '프로필'],
  ['keywords', '키워드'],
  ['alerts', '알림 설정'],
]

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
    <div className="max-w-[1200px] mx-auto px-8 py-7 space-y-5">
      <div className="rise rise-1 flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-extrabold text-strong tracking-[-0.3px]">마이페이지</h1>
          <p className="mt-1 text-[13px] text-muted2">프로필과 구독 키워드, 알림 방식을 관리합니다.</p>
        </div>
        {/* iOS형 세그먼트 */}
        <div className="flex items-center bg-[#eef2f6] rounded-full p-[3px]">
          {TABS.map(([key, label]) => (
            <button
              key={key}
              onClick={() => goTab(key)}
              className={cn(
                'h-[30px] px-4 rounded-full text-[13px] transition-all whitespace-nowrap',
                tab === key ? 'bg-white text-strong font-semibold shadow-seg' : 'text-sub font-medium hover:text-strong'
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="rise rise-2">
        {tab === 'profile' && <ProfileTab onGoTab={goTab} />}
        {tab === 'keywords' && <KeywordsTab />}
        {tab === 'alerts' && <AlertsTab onGoTab={goTab} />}
      </div>
    </div>
  )
}
