import type { StatusType } from '@/types'

export const FIELDS = ['전체', 'IT·소프트웨어', 'AI·데이터', '바이오·헬스', '에너지·환경', '기타·소재', '반도체·전자']
export const STATUS_TYPES: ('전체' | StatusType)[] = ['전체', '접수중', '접수예정', '마감임박', '마감']

/** 대시보드에서 매칭 기준으로 사용하는 내 구독 키워드 */
export const MY_KEYWORDS = ['AI', '플랫폼', '데이터', '스마트시티', '보안']
