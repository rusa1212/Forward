import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { deleteUser, listUsers } from '@/lib/admin'
import { ApiError } from '@/lib/api'
import { logout } from '@/lib/auth'
import type { AdminUser } from '@/types'

/** 관리자 화면 — 가입자(계정) 조회/삭제 */
export function useAdminUsers() {
  const navigate = useNavigate()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const handleError = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 401) {
      logout()
      navigate('/login', { replace: true })
      return
    }
    setError(e instanceof ApiError ? e.message : '가입자 처리 중 오류가 발생했습니다.')
  }, [navigate])

  const refresh = useCallback(async () => {
    try {
      const data = await listUsers()
      setUsers(data)
      setError('')
    } catch (e) {
      handleError(e)
    } finally {
      setLoading(false)
    }
  }, [handleError])

  useEffect(() => {
    refresh()
  }, [refresh])

  const removeUser = useCallback(async (userId: string) => {
    try {
      await deleteUser(userId)
      await refresh()
    } catch (e) {
      handleError(e)
    }
  }, [refresh, handleError])

  return { users, removeUser, loading, error }
}
