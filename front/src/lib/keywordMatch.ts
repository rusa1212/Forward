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
/* Forward 핸드오프 스펙 — 키워드 태그는 뉴트럴 그레이 필(#F2F4F7) 단일 스타일 */
const KEYWORD_COLOR_PALETTE: KeywordColor[] = [
  { bg: 'bg-[#f2f4f7]', text: 'text-body', border: 'border-transparent' },
]

export function getKeywordColor(keyword: string): KeywordColor {
  let hash = 0
  for (let i = 0; i < keyword.length; i++) {
    hash = (hash * 31 + keyword.charCodeAt(i)) | 0
  }
  const index = Math.abs(hash) % KEYWORD_COLOR_PALETTE.length
  return KEYWORD_COLOR_PALETTE[index]
}
