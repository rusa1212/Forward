import { useCallback, useState } from 'react'
import { INITIAL_KEYWORDS } from '@/data/mock/keywords'
import type { Keyword } from '@/types'

/** 마이페이지 키워드 CRUD 로직 */
export function useKeywords() {
  const [keywords, setKeywords] = useState<Keyword[]>(INITIAL_KEYWORDS)

  const addKeyword = useCallback((rawName: string) => {
    const name = rawName.trim()
    if (!name) return false
    let added = false
    setKeywords(prev => {
      if (prev.some(k => k.name === name)) return prev
      added = true
      return [...prev, { id: Date.now(), name, matchCount: 0, dashboardAlert: true, emailAlert: false }]
    })
    return added
  }, [])

  const removeKeyword = useCallback((id: number) => {
    setKeywords(prev => prev.filter(k => k.id !== id))
  }, [])

  const toggleAlert = useCallback((id: number, type: 'dashboard' | 'email') => {
    setKeywords(prev => prev.map(k => k.id !== id ? k : {
      ...k,
      dashboardAlert: type === 'dashboard' ? !k.dashboardAlert : k.dashboardAlert,
      emailAlert: type === 'email' ? !k.emailAlert : k.emailAlert,
    }))
  }, [])

  return { keywords, addKeyword, removeKeyword, toggleAlert }
}

export type KeywordsValue = ReturnType<typeof useKeywords>
