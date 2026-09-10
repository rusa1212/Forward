export default function DDayBadge({ dday }: { dday: number | null }) {
  if (dday === null) return <span className="text-muted2 text-xs whitespace-nowrap">접수 전</span>
  if (dday < 0) return <span className="text-muted2 text-xs whitespace-nowrap">마감</span>
  if (dday <= 1) return <span className="text-danger font-bold text-xs whitespace-nowrap tabular-nums">{dday === 0 ? 'D-day' : 'D-1'}</span>
  if (dday <= 3) return <span className="text-warning text-xs font-semibold whitespace-nowrap tabular-nums">D-{dday}</span>
  return <span className="text-body text-xs font-medium whitespace-nowrap tabular-nums">D-{dday}</span>
}
