import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * 공고 상세 모달을 쿼리스트링(`?detail=3`)으로 열고 닫는다.
 * 새로고침해도 모달이 유지되고, 뒤로가기로 자연스럽게 닫힌다.
 */
export function useDetailModal() {
  const [searchParams, setSearchParams] = useSearchParams()

  const raw = searchParams.get('detail')
  const parsed = raw === null ? NaN : Number(raw)
  const detailId = Number.isInteger(parsed) ? parsed : null

  const openDetail = useCallback((id: number) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('detail', String(id))
      return next
    })
  }, [setSearchParams])

  const closeDetail = useCallback(() => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.delete('detail')
      return next
    }, { replace: true })
  }, [setSearchParams])

  return { detailId, openDetail, closeDetail }
}
