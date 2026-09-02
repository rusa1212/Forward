import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import AlertsDropdown from './AlertsDropdown'
import UserMenu from './UserMenu'
import { isAdmin } from '@/lib/auth'

const NAV_ITEMS: [string, string][] = [
  ['/', '대시보드'],
  ['/search', '공고 검색'],
  ['/mypage', '마이페이지'],
]

export default function Header() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [showAlerts, setShowAlerts] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const admin = isAdmin()

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

  const isActive = (path: string) =>
    path === '/' ? pathname === '/' : pathname === path || pathname.startsWith(`${path}/`)

  return (
    <header className="bg-[#1d3557] h-14 flex items-center px-6 fixed top-0 left-0 right-0 z-40 shadow-md">
      <div className="flex items-center gap-2 mr-8 cursor-pointer" onClick={() => navigate(admin ? '/admin' : '/')}>
        <div className="w-7 h-7 bg-white/20 rounded-lg flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        </div>
        <span className="font-bold text-white text-base tracking-tight">SMS Notice</span>
      </div>

      <nav className="flex gap-0.5 flex-1">
        {!admin && NAV_ITEMS.map(([path, label]) => (
          <button key={path} onClick={() => navigate(path)} className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${isActive(path) ? 'bg-white/20 text-white' : 'text-white/60 hover:text-white hover:bg-white/10'}`}>
            {label}
          </button>
        ))}
      </nav>

      <div className="flex items-center gap-2 relative" ref={menuRef}>
        {/* Bell — 일반 사용자(키워드 알림) 전용, 관리자에게는 표시하지 않음 */}
        {!admin && (
          <button onClick={() => { setShowAlerts(!showAlerts); setShowUserMenu(false) }} className="relative p-2 hover:bg-white/10 rounded-full transition-colors">
            <svg className="w-4.5 h-4.5 text-white" style={{ width: 18, height: 18 }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border border-[#1d3557]" />
          </button>
        )}

        {showAlerts && !admin && <AlertsDropdown onClose={() => setShowAlerts(false)} />}

        <UserMenu
          open={showUserMenu}
          onToggle={() => { setShowUserMenu(!showUserMenu); setShowAlerts(false) }}
          onClose={() => setShowUserMenu(false)}
        />
      </div>
    </header>
  )
}
