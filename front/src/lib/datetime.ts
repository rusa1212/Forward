/**
 * 서버 시각 문자열 처리
 *
 * BE는 DB에 UTC로 저장하고(back/app/db/session.py의 time_zone='+00:00'),
 * FastAPI는 naive datetime을 "2026-09-04T14:37:40" 처럼 **타임존 표기 없이** 직렬화한다.
 * 이 문자열을 그대로 `new Date()`에 넣으면 브라우저가 로컬 시각으로 읽어
 * KST 기준 9시간이 어긋난다. 그래서 표기가 없으면 UTC로 간주하고 붙여준다.
 *
 * (docs/api-contract-v1.md 1-5절)
 */
const HAS_TIMEZONE = /(?:Z|[+-]\d{2}:?\d{2})$/i

export function parseServerDate(value: string): Date {
  const trimmed = value.trim()
  const normalized = HAS_TIMEZONE.test(trimmed) ? trimmed : `${trimmed}Z`
  return new Date(normalized)
}

const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

/**
 * "방금 전" / "12분 전" / "3시간 전" / "어제" / "3일 전" / "2026.09.01"
 *
 * 알림 목록의 상대 시간 표기용. 서버는 절대 시각(createdAt)만 내려주고
 * 이 가공은 FE 몫이다 (docs/api-contract-v1.md 9-1절).
 */
export function formatRelativeTime(value: string, now: number = Date.now()): string {
  const date = parseServerDate(value)
  const time = date.getTime()
  if (Number.isNaN(time)) return ''

  const diff = now - time
  if (diff < MINUTE) return '방금 전'
  if (diff < HOUR) return `${Math.floor(diff / MINUTE)}분 전`
  if (diff < DAY) return `${Math.floor(diff / HOUR)}시간 전`
  if (diff < 2 * DAY) return '어제'
  if (diff < 7 * DAY) return `${Math.floor(diff / DAY)}일 전`

  // 일주일이 넘으면 상대 표기가 오히려 읽기 어려워 날짜를 그대로 보여준다
  return date.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
