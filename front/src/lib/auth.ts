/** 로그인 토큰(JWT) 저장/조회. back/app/api/v1/auth.py의 로그인 응답 토큰을 그대로 저장한다. */
const TOKEN_KEY = 'sms-notice-auth-token'
const ADMIN_KEY = 'sms-notice-auth-is-admin'
const NAME_KEY = 'sms-notice-auth-name'

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function isAuthenticated() {
  return getToken() !== null
}

export function isAdmin() {
  return sessionStorage.getItem(ADMIN_KEY) === '1'
}

export function getName(): string {
  return sessionStorage.getItem(NAME_KEY) ?? ''
}

export function login(token: string, isAdminUser: boolean, name: string) {
  sessionStorage.setItem(TOKEN_KEY, token)
  sessionStorage.setItem(ADMIN_KEY, isAdminUser ? '1' : '0')
  sessionStorage.setItem(NAME_KEY, name)
}

export function logout() {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(ADMIN_KEY)
  sessionStorage.removeItem(NAME_KEY)
}
