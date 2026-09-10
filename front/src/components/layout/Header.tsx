import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Bell, ExternalLink } from 'lucide-react'
import { cn } from '@/lib/utils'
import AlertsDropdown from './AlertsDropdown'
import UserMenu from './UserMenu'
import { getName, isAdmin, isAuthenticated, logout } from '@/lib/auth'
import { useNotifications } from '@/hooks/useNotifications'
import logoCompact from '@/assets/brand/forward-logo-compact.svg'

const NAV_ITEMS: [string, string][] = [
  ['/dashboard', '대시보드'],
  ['/search', '공고 검색'],
  ['/mypage', '마이페이지'],
]

const EXTERNAL_PORTALS: [string, string][] = [
  ['NTIS', 'https://www.ntis.go.kr'],
  ['IRIS', 'https://www.iris.go.kr'],
  ['K-Startup', 'https://www.k-startup.go.kr'],
  ['나라장터', 'https://www.g2b.go.kr'],
]

export default function Header() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [showAlerts, setShowAlerts] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const authed = isAuthenticated()
  const admin = isAdmin()
  const name = getName()

  // 배지(안읽음 개수)와 드롭다운 목록이 같은 데이터를 봐야 해서 여기서 한 번만 부른다.
  // 비로그인/관리자에게는 종 아이콘이 없으므로 조회하지 않는다.
  const notifications = useNotifications(authed && !admin)

  /** 종 아이콘 토글. 열 때마다 최신 알림을 다시 받아온다. */
  const toggleAlerts = () => {
    const next = !showAlerts
    setShowAlerts(next)
    setShowUserMenu(false)
    if (next) notifications.refresh()
  }

  // 헤더 바깥을 클릭하면 열려 있는 드롭다운을 닫는다
  useEffect(() => {
    if (!showAlerts && !showUserMenu) return
    const onPointerDown = (e: MouseEvent) => {
      if (menuRef.current?.contains(e.target as Node)) return
      setShowAlerts(false)
      setShowUserMenu(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [showAlerts, showUserMenu])

  const isActive = (path: string) => pathname === path || pathname.startsWith(`${path}/`)

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      {/* 유틸리티 바 */}
      <div className="bg-canvas border-b border-line">
        <div className="max-w-[1200px] mx-auto px-8 h-9 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {EXTERNAL_PORTALS.map(([label, url]) => (
              <a
                key={label}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-xs text-sub hover:text-strong transition-colors"
              >
                {label}
                <ExternalLink className="w-2.5 h-2.5 opacity-60" strokeWidth={2} />
              </a>
            ))}
          </div>
          {authed ? (
            <button onClick={handleLogout} className="text-xs font-medium text-primary2 hover:text-primary-hover transition-colors">
              로그아웃
            </button>
          ) : (
            <button onClick={() => navigate('/login')} className="text-xs font-medium text-primary2 hover:text-primary-hover transition-colors">
              로그인
            </button>
          )}
        </div>
      </div>

      {/* GNB */}
      <header className="sticky top-0 z-40 h-[62px] bg-white/[0.92] backdrop-blur-md border-b border-line">
        <div className="max-w-[1200px] mx-auto px-8 h-full flex items-center justify-between">
          <div className="flex items-center gap-10">
            <button className="pressable" onClick={() => navigate(admin ? '/admin' : '/')}>
              <img src={logoCompact} alt="Forward — R&D Monitor" className="h-[30px] w-auto" />
            </button>
            {authed && !admin && (
              <nav className="flex items-center gap-7">
                {NAV_ITEMS.map(([path, label]) => (
                  <button
                    key={path}
                    onClick={() => navigate(path)}
                    className={cn(
                      'text-[15px] font-semibold transition-colors',
                      isActive(path) ? 'text-primary2' : 'text-[#44506b] hover:text-strong'
                    )}
                  >
                    {label}
                  </button>
                ))}
              </nav>
            )}
          </div>

          {authed ? (
            <div className="flex items-center gap-4 relative" ref={menuRef}>
              {!admin && (
                <button
                  onClick={toggleAlerts}
                  aria-label={notifications.unreadCount > 0 ? `알림 ${notifications.unreadCount}건` : '알림'}
                  className="pressable relative p-1.5 rounded-lg hover:bg-subtle transition-colors"
                >
                  <Bell className="w-[22px] h-[22px] text-[#44506b]" strokeWidth={1.8} />
                  {notifications.unreadCount > 0 && (
                    <span className="absolute -top-0.5 -right-0.5 min-w-4 h-4 px-1 rounded-full bg-danger text-white text-[10px] font-bold flex items-center justify-center">
                      {notifications.unreadCount > 99 ? '99+' : notifications.unreadCount}
                    </span>
                  )}
                </button>
              )}
              {showAlerts && !admin && <AlertsDropdown onClose={() => setShowAlerts(false)} notifications={notifications} />}

              <button
                onClick={() => { setShowUserMenu(!showUserMenu); setShowAlerts(false) }}
                className="pressable flex items-center gap-2.5"
              >
                <span className="w-8 h-8 rounded-full bg-soft text-primary2 text-[13px] font-bold flex items-center justify-center">
                  {name.charAt(0)}
                </span>
                <span className="text-sm font-medium text-strong">{name}</span>
              </button>
              <UserMenu open={showUserMenu} onToggle={() => { setShowUserMenu(!showUserMenu); setShowAlerts(false) }} onClose={() => setShowUserMenu(false)} />
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <button onClick={() => navigate('/login')} className="text-[15px] font-semibold text-[#44506b] hover:text-strong transition-colors">
                로그인
              </button>
              <button
                onClick={() => navigate('/signup')}
                className="pressable h-10 px-5 rounded-[10px] bg-primary2 hover:bg-primary-hover text-white text-sm font-semibold transition-colors"
              >
                시작하기
              </button>
            </div>
          )}
        </div>
      </header>
    </>
  )
}
