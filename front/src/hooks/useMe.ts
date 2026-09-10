import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '@/lib/api'
import { logout } from '@/lib/auth'
import { changePassword, getMe, updateMyEmail } from '@/lib/me'
import type { Me } from '@/types'

/** 토큰이 죽었다는 뜻의 401 코드. api.ts의 TOKEN_INVALID_CODES와 같은 기준이다. */
const TOKEN_INVALID_CODES = new Set(['UNAUTHORIZED', 'INVALID_TOKEN'])

/**
 * 마이페이지 — 내 정보 조회/수정, 비밀번호 변경
 *
 * BE에서 고칠 수 있는 건 이메일 하나뿐이라 이 훅이 다루는 변경도 이메일과
 * 비밀번호 두 가지다. 이름·부서·사번은 조회만 한다.
 */
export function useMe() {
  const navigate = useNavigate()
  const [me, setMe] = useState<Me | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  /** 수정·비밀번호 변경 요청 진행 중 — 버튼 중복 클릭 방지용 */
  const [pending, setPending] = useState(false)

  /**
   * 401이라고 무조건 로그인으로 보내면 안 된다 —
   * 비밀번호 변경 시 현재 비밀번호 오답도 401(INVALID_CREDENTIALS)이라
   * 잘못 입력한 사용자가 로그인 화면으로 튕긴다. 코드로 구분한다.
   */
  const isSessionDead = (e: unknown) =>
    e instanceof ApiError && e.status === 401 && TOKEN_INVALID_CODES.has(e.code)

  const bounceToLogin = useCallback(() => {
    logout()
    navigate('/login', { replace: true })
  }, [navigate])

  const refresh = useCallback(async () => {
    try {
      setMe(await getMe())
      setError('')
    } catch (e) {
      if (isSessionDead(e)) {
        bounceToLogin()
        return
      }
      setError(e instanceof ApiError ? e.message : '내 정보를 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }, [bounceToLogin])

  useEffect(() => {
    refresh()
  }, [refresh])

  /** 성공하면 빈 문자열, 실패하면 화면에 띄울 사유를 돌려준다. */
  const saveEmail = useCallback(async (rawEmail: string): Promise<string> => {
    const email = rawEmail.trim()
    if (!email) return '이메일을 입력해주세요.'
    if (pending) return ''

    setPending(true)
    try {
      setMe(await updateMyEmail(email))
      return ''
    } catch (e) {
      if (isSessionDead(e)) {
        bounceToLogin()
        return ''
      }
      return e instanceof ApiError ? e.message : '이메일을 변경하지 못했습니다.'
    } finally {
      setPending(false)
    }
  }, [pending, bounceToLogin])

  /** 성공하면 빈 문자열, 실패하면 화면에 띄울 사유를 돌려준다. */
  const savePassword = useCallback(async (
    currentPw: string,
    newPw: string,
    confirmPw: string,
    minLength: number,
  ): Promise<string> => {
    if (!currentPw) return '현재 비밀번호를 입력해주세요.'
    if (newPw.length < minLength) return `새 비밀번호는 ${minLength}자 이상이어야 합니다.`
    if (newPw !== confirmPw) return '새 비밀번호가 서로 일치하지 않습니다.'
    if (newPw === currentPw) return '현재 비밀번호와 다른 비밀번호를 입력해주세요.'
    if (pending) return ''

    setPending(true)
    try {
      await changePassword(currentPw, newPw)
      return ''
    } catch (e) {
      if (isSessionDead(e)) {
        bounceToLogin()
        return ''
      }
      // 현재 비밀번호 오답(401 INVALID_CREDENTIALS)은 여기로 온다 — 로그인 상태는 유지된다
      return e instanceof ApiError ? e.message : '비밀번호를 변경하지 못했습니다.'
    } finally {
      setPending(false)
    }
  }, [pending, bounceToLogin])

  return { me, loading, error, pending, refresh, saveEmail, savePassword }
}
