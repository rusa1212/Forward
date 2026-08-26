import type { StatusType } from '@/types'

export default function StatusBadge({ status }: { status: StatusType }) {
  const styles: Record<StatusType, string> = {
    '접수중': 'bg-blue-100 text-blue-700',
    '접수예정': 'bg-gray-100 text-gray-600',
    '마감임박': 'bg-red-100 text-red-600',
    '마감': 'bg-gray-100 text-gray-400',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}
