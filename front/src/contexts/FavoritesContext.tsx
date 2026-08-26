import { createContext, useContext } from 'react'
import { useFavorites, type FavoritesValue } from '@/hooks/useFavorites'

const FavoritesContext = createContext<FavoritesValue | null>(null)

export function FavoritesProvider({ children }: { children: React.ReactNode }) {
  const value = useFavorites()
  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>
}

export function useFavoritesContext() {
  const ctx = useContext(FavoritesContext)
  if (!ctx) throw new Error('useFavoritesContext는 FavoritesProvider 안에서만 사용할 수 있습니다.')
  return ctx
}
