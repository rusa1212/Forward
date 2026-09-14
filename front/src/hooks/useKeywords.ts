import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/lib/api'
import { logout } from '@/lib/auth'
import type { Keyword } from '@/types'

/** back/app/api/v1/keywords.py의 _serialize()가 실제로 내려주는 필드. */
interface ApiKeyword {
  id: string
  keyword: string
  createdAt: string
  dashboardAlert: boolean
  emailAlert: boolean
  matchCount: number
}

function mapKeyword(raw: ApiKeyword): Keyword {
  return {
    id: raw.id,
    name: raw.keyword,
    matchCount: raw.matchCount,
    dashboardAlert: raw.dashboardAlert,
    emailAlert: raw.emailAlert,
  }
}

/** 마이페이지 키워드 CRUD 로직 */
export function useKeywords() {
  const navigate = useNavigate()
  const [keywords, setKeywords] = useState<Keyword[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const handleError = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 401) {
      logout()
      navigate('/login', { replace: true })
      return
    }
    setError(e instanceof ApiError ? e.message : '키워드 처리 중 오류가 발생했습니다.')
  }, [navigate])

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get<ApiKeyword[]>('/keywords')
      setKeywords(data.map(mapKeyword))
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

  const addKeyword = useCallback(async (rawName: string) => {
    const name = rawName.trim()
    if (!name) return false
    try {
      await api.post('/keywords', { keyword: name })
      await refresh()
      return true
    } catch (e) {
      handleError(e)
      return false
    }
  }, [refresh, handleError])

  const removeKeyword = useCallback(async (id: string) => {
    try {
      await api.delete(`/keywords/${id}`)
      await refresh()
    } catch (e) {
      handleError(e)
    }
  }, [refresh, handleError])

  /** 대시보드/이메일 알림 on-off. PATCH /keywords/{id}/alerts로 저장하고, 응답값으로 갱신한다. */
  const toggleAlert = useCallback(async (id: string, type: 'dashboard' | 'email') => {
    const target = keywords.find(k => k.id === id)
    if (!target) return
    const body = type === 'dashboard'
      ? { dashboardAlert: !target.dashboardAlert }
      : { emailAlert: !target.emailAlert }
    try {
      const { data } = await api.patch<ApiKeyword>(`/keywords/${id}/alerts`, body)
      setKeywords(prev => prev.map(k => k.id === id ? mapKeyword(data) : k))
    } catch (e) {
      handleError(e)
    }
  }, [keywords, handleError])

  /** 알림설정 화면의 "이메일 발송" 토글 하나로 모든 키워드의 emailAlert를 한 번에 맞춘다.
   * 키워드마다 따로 토글을 두면 개수가 많아져 헷갈리기 때문에(알림설정 UI 참고), 이미
   * 원하는 값인 키워드는 건드리지 않고 나머지만 PATCH한다. DB에는 여전히 키워드별 컬럼이라
   * API 자체는 그대로 재사용한다. */
  const setAllEmailAlerts = useCallback(async (enabled: boolean) => {
    const targets = keywords.filter(k => k.emailAlert !== enabled)
    if (targets.length === 0) return
    try {
      await Promise.all(targets.map(k => api.patch<ApiKeyword>(`/keywords/${k.id}/alerts`, { emailAlert: enabled })))
      await refresh()
    } catch (e) {
      handleError(e)
    }
  }, [keywords, refresh, handleError])

  return { keywords, addKeyword, removeKeyword, toggleAlert, setAllEmailAlerts, loading, error }
}

export type KeywordsValue = ReturnType<typeof useKeywords>
