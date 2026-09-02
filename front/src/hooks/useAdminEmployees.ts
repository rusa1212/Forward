import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createEmployee, deleteEmployee, listEmployees } from '@/lib/admin'
import { ApiError } from '@/lib/api'
import { logout } from '@/lib/auth'
import type { AdminEmployee } from '@/types'

/** 관리자 화면 — 사원 명부 조회/등록/삭제 */
export function useAdminEmployees() {
  const navigate = useNavigate()
  const [employees, setEmployees] = useState<AdminEmployee[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const handleError = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 401) {
      logout()
      navigate('/login', { replace: true })
      return
    }
    setError(e instanceof ApiError ? e.message : '사원 명부 처리 중 오류가 발생했습니다.')
  }, [navigate])

  const refresh = useCallback(async () => {
    try {
      const data = await listEmployees()
      setEmployees(data)
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

  const addEmployee = useCallback(async (body: { empId: string; name: string; department?: string }) => {
    try {
      await createEmployee(body)
      await refresh()
      return true
    } catch (e) {
      handleError(e)
      return false
    }
  }, [refresh, handleError])

  const removeEmployee = useCallback(async (empId: string) => {
    try {
      await deleteEmployee(empId)
      await refresh()
    } catch (e) {
      handleError(e)
    }
  }, [refresh, handleError])

  return { employees, addEmployee, removeEmployee, loading, error }
}
