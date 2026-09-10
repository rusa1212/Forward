import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { motion } from 'motion/react'
import { isAdmin, logout } from '@/lib/auth'

/** 드롭다운 전용 — 트리거(아바타 버튼)는 Header가 렌더링한다. */
export default function UserMenu({ open, onClose }: {
  open: boolean
  onToggle: () => void
  onClose: () => void
}) {
  const navigate = useNavigate()
  const admin = isAdmin()

  const handleLogout = () => {
    logout()
    onClose()
    navigate('/login', { replace: true })
  }

  if (!open) return null

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96, y: -4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: 'spring', bounce: 0, duration: 0.3 }}
      style={{ transformOrigin: 'top right' }}
      className="absolute top-12 right-0 w-44 bg-surface rounded-xl border border-line shadow-float z-50 overflow-hidden py-1"
    >
      {!admin && (
        <button onClick={() => { navigate('/mypage'); onClose() }} className="w-full px-4 py-2.5 text-left text-sm text-strong hover:bg-subtle transition-colors">
          마이페이지
        </button>
      )}
      {admin && (
        <button onClick={() => { navigate('/admin'); onClose() }} className="w-full px-4 py-2.5 text-left text-sm text-strong hover:bg-subtle transition-colors">
          관리자 페이지
        </button>
      )}
      <div className="h-px bg-line mx-2" />
      <button onClick={handleLogout} className="w-full px-4 py-2.5 text-left text-sm text-danger hover:bg-[rgba(240,68,56,0.06)] transition-colors flex items-center gap-2">
        <LogOut className="w-3.5 h-3.5" strokeWidth={1.8} />
        로그아웃
      </button>
    </motion.div>
  )
}
