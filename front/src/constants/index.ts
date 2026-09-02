import type { SortType, StatusType } from '@/types'

export const FIELDS = ['전체', 'IT·소프트웨어', 'AI·데이터', '바이오·헬스', '에너지·환경', '기타·소재', '반도체·전자']
export const STATUS_TYPES: ('전체' | StatusType)[] = ['전체', '접수중', '접수예정', '마감임박', '마감']
export const SORT_OPTIONS: [SortType, string][] = [
  ['latest', '최신순'],
  ['deadline', '마감순'],
  ['title', '제목순'],
]
