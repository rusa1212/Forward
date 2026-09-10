import type { StatusType } from '@/types'

/** 시맨틱 컬러는 텍스트에만 — 배경 채움 없이 색 텍스트로 상태를 표시한다. */
export default function StatusBadge({ status }: { status: StatusType }) {
  const styles: Record<StatusType, string> = {
    '접수중': 'text-success',
    '접수예정': 'text-sub',
    '마감임박': 'text-warning',
    '마감': 'text-muted2',
  }
  return (
    <span className={`inline-flex items-center text-[13px] font-semibold whitespace-nowrap ${styles[status]}`}>
      {status}
    </span>
  )
}
