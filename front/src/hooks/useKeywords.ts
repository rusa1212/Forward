import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/lib/api'
import { logout } from '@/lib/auth'
import type { Keyword } from '@/types'

/** back/app/api/v1/keywords.py의 _serialize()가 실제로 내려주는 필드 (keyword, id, createdAt뿐). */
interface ApiKeyword {
  id: string
  keyword: string
  createdAt: string
}

function mapKeyword(raw: ApiKeyword): Keyword {
  return { id: raw.id, name: raw.keyword, matchCount: 0, dashboardAlert: true, emailAlert: false }
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

  /**
   * 대시보드/이메일 알림 on-off는 BE에 아직 API가 없다 (alert_settings 테이블/엔드포인트가
   * 다음 작업). 그래서 로컬 상태만 바뀌고 서버에는 저장되지 않는다 — 새로고침하면 초기화된다.
   */
  const toggleAlert = useCallback((id: string, type: 'dashboard' | 'email') => {
    setKeywords(prev => prev.map(k => k.id !== id ? k : {
      ...k,
      dashboardAlert: type === 'dashboard' ? !k.dashboardAlert : k.dashboardAlert,
      emailAlert: type === 'email' ? !k.emailAlert : k.emailAlert,
    }))
  }, [])

  return { keywords, addKeyword, removeKeyword, toggleAlert, loading, error }
}

export type KeywordsValue = ReturnType<typeof useKeywords>
