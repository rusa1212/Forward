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
}

function mapKeyword(raw: ApiKeyword): Keyword {
  // matchCount(키워드별 매칭 건수)는 alert_settings와 성격이 다른 별도 집계값이라
  // 이번 범위 밖이다 (docs/fe/alert-settings-API-제안.md 6-4절) — 여전히 0 고정.
  return {
    id: raw.id,
    name: raw.keyword,
    matchCount: 0,
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

  return { keywords, addKeyword, removeKeyword, toggleAlert, loading, error }
}

export type KeywordsValue = ReturnType<typeof useKeywords>
