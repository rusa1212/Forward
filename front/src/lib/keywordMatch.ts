import type { Announcement } from '@/types'

/**
 * 공고 제목(+요약)에 포함된 사용자 키워드를 부분 문자열 매칭으로 찾는다.
 * BE는 relatedKeywords를 채워주지 않으므로 FE에서 직접 계산한다.
 */
export function matchKeywords(a: Announcement, keywordNames: string[]): string[] {
  const haystack = a.title + (a.originalText ?? '')
  const matched = keywordNames.filter(k => k && haystack.includes(k))
  return Array.from(new Set(matched))
}
