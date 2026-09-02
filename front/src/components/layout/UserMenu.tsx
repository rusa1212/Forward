import { useNavigate } from 'react-router-dom'
import { getName, isAdmin, logout } from '@/lib/auth'

export default function UserMenu({ open, onToggle, onClose }: {
  open: boolean
  onToggle: () => void
  onClose: () => void
}) {
  const navigate = useNavigate()
  const name = getName()

  const handleLogout = () => {
    logout()
    onClose()
    navigate('/login', { replace: true })
  }

  return (
    <>
      <button onClick={onToggle} className="flex items-center gap-2 hover:bg-white/10 rounded-lg px-2.5 py-1.5 transition-colors">
        <div className="w-7 h-7 bg-[#457b9d] rounded-full flex items-center justify-center text-white text-xs font-bold">{name.charAt(0)}</div>
        <span className="text-sm text-white font-medium">{name}</span>
        <svg className="w-3 h-3 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute top-11 right-0 w-40 bg-white rounded-xl shadow-2xl border border-gray-100 z-50 overflow-hidden py-1">
          <button onClick={() => { navigate('/mypage'); onClose() }} className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors">마이페이지</button>
          {isAdmin() && (
            <button onClick={() => { navigate('/admin'); onClose() }} className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors">관리자 페이지</button>
          )}
          <div className="h-px bg-gray-100 mx-2" />
          <button onClick={handleLogout} className="w-full px-4 py-2.5 text-left text-sm text-red-500 hover:bg-red-50 transition-colors">로그아웃</button>
        </div>
      )}
    </>
  )
}
