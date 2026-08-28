import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '@/lib/api'
import { logout } from '@/lib/auth'

/** back/app/api/v1/saved_announcements.py의 _serialize()가 실제로 내려주는 필드. */
interface ApiSavedAnnouncement {
  id: string
  savedAt: string
  announcement: { id: string }
}

/** 즐겨찾기(저장한 공고) 상태와 토글 로직 */
export function useFavorites() {
  const navigate = useNavigate()
  const [favorites, setFavorites] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)

  const handleError = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 401) {
      logout()
      navigate('/login', { replace: true })
    }
    // 401 외 오류(예: 대시보드 mock 공고에 대한 저장 시도로 생기는 404)는 조용히 무시한다.
  }, [navigate])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api.get<ApiSavedAnnouncement[]>('/saved-announcements')
      .then(({ data }) => {
        if (!cancelled) setFavorites(new Set(data.map(row => row.announcement.id)))
      })
      .catch(handleError)
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [handleError])

  const toggleFavorite = useCallback(async (id: string) => {
    const currentlySaved = favorites.has(id)
    try {
      if (currentlySaved) {
        await api.delete(`/saved-announcements/${id}`)
      } else {
        await api.post('/saved-announcements', { announcementId: id })
      }
      setFavorites(prev => {
        const next = new Set(prev)
        if (currentlySaved) next.delete(id)
        else next.add(id)
        return next
      })
    } catch (e) {
      handleError(e)
    }
  }, [favorites, handleError])

  const isFavorite = useCallback((id: string) => favorites.has(id), [favorites])

  return { favorites, toggleFavorite, isFavorite, loading }
}

export type FavoritesValue = ReturnType<typeof useFavorites>
