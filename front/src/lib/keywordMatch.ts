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

export interface KeywordColor {
  bg: string
  text: string
  border: string
}

/** 값(키워드 문자열) 기반 고정 팔레트 — 등록 순서와 무관하게 같은 키워드는 항상 같은 색이 나온다. */
const KEYWORD_COLOR_PALETTE: KeywordColor[] = [
  { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-100' },
  { bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-100' },
  { bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-100' },
  { bg: 'bg-amber-50', text: 'text-amber-600', border: 'border-amber-100' },
  { bg: 'bg-rose-50', text: 'text-rose-600', border: 'border-rose-100' },
  { bg: 'bg-teal-50', text: 'text-teal-600', border: 'border-teal-100' },
  { bg: 'bg-indigo-50', text: 'text-indigo-600', border: 'border-indigo-100' },
  { bg: 'bg-orange-50', text: 'text-orange-600', border: 'border-orange-100' },
]

export function getKeywordColor(keyword: string): KeywordColor {
  let hash = 0
  for (let i = 0; i < keyword.length; i++) {
    hash = (hash * 31 + keyword.charCodeAt(i)) | 0
  }
  const index = Math.abs(hash) % KEYWORD_COLOR_PALETTE.length
  return KEYWORD_COLOR_PALETTE[index]
}
