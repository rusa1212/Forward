export default function StatsGrid({ matchedCount, newTodayCount, urgentCount, savedCount }: {
  matchedCount: number
  newTodayCount: number
  urgentCount: number
  savedCount: number
}) {
  const stats = [
    { label: '매칭 공고', value: matchedCount, sub: '내 키워드 기준', highlight: false },
    { label: '오늘 신규', value: newTodayCount, sub: '오늘 접수 시작', highlight: newTodayCount > 0 },
    { label: '마감 임박', value: urgentCount, sub: 'D-3 이내', highlight: urgentCount > 0, urgent: true },
    { label: '저장한 공고', value: savedCount, sub: '즐겨찾기 목록', highlight: false },
  ]

  return (
    <div className="grid grid-cols-4 gap-4">
      {stats.map(s => (
        <div key={s.label} className={`bg-white rounded-xl p-4 shadow-sm border ${s.urgent && s.highlight ? 'border-red-200 bg-red-50' : 'border-gray-100'}`}>
          <p className={`text-2xl font-bold ${s.urgent && s.highlight ? 'text-red-500' : s.highlight ? 'text-[#1d3557]' : 'text-gray-700'}`}>{s.value}</p>
          <p className="text-xs font-semibold text-gray-600 mt-0.5">{s.label}</p>
          <p className="text-[10px] text-gray-400 mt-0.5">{s.sub}</p>
        </div>
      ))}
    </div>
  )
}
