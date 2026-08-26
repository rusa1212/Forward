import { createContext, useContext } from 'react'
import { useKeywords, type KeywordsValue } from '@/hooks/useKeywords'

const KeywordsContext = createContext<KeywordsValue | null>(null)

export function KeywordsProvider({ children }: { children: React.ReactNode }) {
  const value = useKeywords()
  return <KeywordsContext.Provider value={value}>{children}</KeywordsContext.Provider>
}

export function useKeywordsContext() {
  const ctx = useContext(KeywordsContext)
  if (!ctx) throw new Error('useKeywordsContext는 KeywordsProvider 안에서만 사용할 수 있습니다.')
  return ctx
}
