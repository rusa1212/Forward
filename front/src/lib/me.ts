import { api } from './api'
import type { Me } from '@/types'

/**
 * 마이페이지 — 내 정보 조회/수정, 비밀번호 변경.
 * back/app/api/v1/me.py. 모두 토큰 필요. (docs/api-contract-v1.md 8절)
 */

export function getMe() {
  return api.get<Me>('/me').then(({ data }) => data)
}

/**
 * 내 정보 수정. BE가 받는 필드는 email 뿐이다 —
 * 이름·부서는 employees 테이블 소유이고, 연락처·아이디는 스키마에 아예 없다.
 *
 * 다른 계정이 쓰는 이메일이면 ApiError(409, 'DUPLICATE_EMAIL')
 */
export function updateMyEmail(email: string) {
  return api.patch<Me>('/me', { email }).then(({ data }) => data)
}

/**
 * 비밀번호 변경. 새 비밀번호는 6자 이상이어야 한다(BE 검증).
 *
 * 현재 비밀번호가 틀리면 ApiError(401, 'INVALID_CREDENTIALS')다.
 * **토큰 만료가 아니므로 로그아웃시키면 안 된다** — api.ts가 코드로 구분하고,
 * 화면 쪽에서도 401을 무조건 로그인 이동으로 처리하지 않아야 한다.
 */
export function changePassword(currentPw: string, newPw: string) {
  return api
    .post<{ message: string }>('/me/change-password', { currentPw, newPw })
    .then(({ data }) => data)
}

/** BE가 요구하는 새 비밀번호 최소 길이 (me.py의 ChangePasswordRequest) */
export const MIN_PASSWORD_LENGTH = 6
