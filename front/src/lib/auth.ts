/** 로그인 토큰(JWT) 저장/조회. back/app/api/v1/auth.py의 로그인 응답 토큰을 그대로 저장한다. */
const TOKEN_KEY = 'sms-notice-auth-token'

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function isAuthenticated() {
  return getToken() !== null
}

export function login(token: string) {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function logout() {
  sessionStorage.removeItem(TOKEN_KEY)
}
