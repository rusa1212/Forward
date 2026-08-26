export default function Pagination({ currentPage, totalPages, onChange }: {
  currentPage: number
  totalPages: number
  onChange: (page: number) => void
}) {
  if (totalPages <= 1) return null

  return (
    <div className="px-5 py-3.5 border-t border-gray-100 flex items-center justify-center gap-1">
      <button onClick={() => onChange(Math.max(1, currentPage - 1))} disabled={currentPage === 1} className="px-3 py-1.5 text-xs rounded-lg hover:bg-gray-100 disabled:opacity-30 transition-colors text-gray-600">이전</button>
      {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
        <button key={p} onClick={() => onChange(p)} className={`w-8 h-8 text-xs rounded-lg transition-colors ${currentPage === p ? 'bg-[#1d3557] text-white' : 'hover:bg-gray-100 text-gray-600'}`}>{p}</button>
      ))}
      <button onClick={() => onChange(Math.min(totalPages, currentPage + 1))} disabled={currentPage === totalPages} className="px-3 py-1.5 text-xs rounded-lg hover:bg-gray-100 disabled:opacity-30 transition-colors text-gray-600">다음</button>
    </div>
  )
}
