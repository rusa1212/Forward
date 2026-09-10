import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '@/lib/api'
import { getAlertSettings, saveAlertSettings } from '@/lib/alertSettings'
import { logout } from '@/lib/auth'
import type { AlertSettings } from '@/types'

const TOKEN_INVALID_CODES = new Set(['UNAUTHORIZED', 'INVALID_TOKEN'])

/** 마이페이지 알림 설정 — 조회/저장. AlertsTab의 저장 버튼이 이 훅의 save를 호출한다. */
export function useAlertSettings() {
  const navigate = useNavigate()
  const [settings, setSettings] = useState<AlertSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  const isSessionDead = (e: unknown) =>
    e instanceof ApiError && e.status === 401 && TOKEN_INVALID_CODES.has(e.code)

  const bounceToLogin = useCallback(() => {
    logout()
    navigate('/login', { replace: true })
  }, [navigate])

  const refresh = useCallback(async () => {
    try {
      setSettings(await getAlertSettings())
      setError('')
    } catch (e) {
      if (isSessionDead(e)) {
        bounceToLogin()
        return
      }
      setError(e instanceof ApiError ? e.message : '알림 설정을 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }, [bounceToLogin])

  useEffect(() => {
    refresh()
  }, [refresh])

  /** 성공하면 빈 문자열, 실패하면 화면에 띄울 사유를 돌려준다 (useMe의 saveEmail과 같은 결). */
  const save = useCallback(async (next: AlertSettings): Promise<string> => {
    if (pending) return ''
    setPending(true)
    try {
      setSettings(await saveAlertSettings(next))
      return ''
    } catch (e) {
      if (isSessionDead(e)) {
        bounceToLogin()
        return ''
      }
      return e instanceof ApiError ? e.message : '알림 설정을 저장하지 못했습니다.'
    } finally {
      setPending(false)
    }
  }, [pending, bounceToLogin])

  return { settings, loading, error, pending, save }
}
