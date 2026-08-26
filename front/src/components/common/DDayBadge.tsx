export default function DDayBadge({ dday }: { dday: number }) {
  if (dday < 0) return <span className="text-gray-400 text-xs">마감</span>
  if (dday === 0) return <span className="text-red-600 font-bold text-xs">D-day</span>
  if (dday <= 3) return <span className="text-red-500 text-xs font-medium">D-{dday}</span>
  return <span className="text-gray-500 text-xs">D-{dday}</span>
}
