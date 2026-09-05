import { getToken, logout } from './auth'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

interface ApiErrorBody {
  success: false
  error: { code: string; message: string }
}

interface ApiSuccessBody<T> {
  success: true
  data: T
  meta?: Record<string, unknown>
}

/**
 * 토큰이 죽었다는 뜻의 401 코드.
 *
 * 401을 무조건 로그아웃으로 처리하면 안 된다 — 로그인 실패(INVALID_CREDENTIALS)와
 * 비밀번호 변경 시 현재 비밀번호 오답도 같은 401이라, 잘못 입력한 사용자가
 * 그대로 로그아웃된다. (docs/api-contract-v1.md 11절)
 */
const TOKEN_INVALID_CODES = new Set(['UNAUTHORIZED', 'INVALID_TOKEN'])

/** BE 공통 오류 응답({"success": false, "error": {code, message}})을 담아 던지는 예외. */
export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<ApiSuccessBody<T>> {
  const headers = new Headers(options.headers)
  if (options.body) headers.set('Content-Type', 'application/json')
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', '서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.')
  }

  const body = await res.json().catch(() => null)

  if (!res.ok || !body || body.success === false) {
    const err = body as ApiErrorBody | null
    const code = err?.error?.code ?? 'UNKNOWN_ERROR'

    // 토큰이 만료·위조된 경우에만 로그인 상태를 비운다
    if (res.status === 401 && TOKEN_INVALID_CODES.has(code)) logout()

    throw new ApiError(
      res.status,
      code,
      err?.error?.message ?? '요청 처리 중 오류가 발생했습니다.'
    )
  }

  return body as ApiSuccessBody<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body === undefined ? undefined : JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
