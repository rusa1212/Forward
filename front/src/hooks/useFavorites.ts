import { useCallback, useState } from 'react'
import { ANNOUNCEMENTS } from '@/data/mock/announcements'

/** 즐겨찾기(저장한 공고) 상태와 토글 로직 */
export function useFavorites() {
  const [favorites, setFavorites] = useState<Set<number>>(
    () => new Set(ANNOUNCEMENTS.filter(a => a.isFavorite).map(a => a.id))
  )

  const toggleFavorite = useCallback((id: number) => {
    setFavorites(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const isFavorite = useCallback((id: number) => favorites.has(id), [favorites])

  return { favorites, toggleFavorite, isFavorite }
}

export type FavoritesValue = ReturnType<typeof useFavorites>
