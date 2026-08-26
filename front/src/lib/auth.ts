/** 데모 수준의 인증 — 세션스토리지 플래그 하나로만 로그인 여부를 판단한다. */
const KEY = 'sms-notice-auth'

export function isAuthenticated() {
  return sessionStorage.getItem(KEY) === '1'
}

export function login() {
  sessionStorage.setItem(KEY, '1')
}

export function logout() {
  sessionStorage.removeItem(KEY)
}
