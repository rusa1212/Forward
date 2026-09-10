// TODO(backend): 매칭 추이 집계 API가 아직 없어 임시 샘플 데이터로 렌더링한다.
// GET /dashboard/trend 같은 월별 매칭 건수 API가 생기면 SAMPLE_* 를 실데이터로 교체할 것.
const MONTHS = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']
const SAMPLE_2025 = [4, 6, 5, 8, 7, 9, 8, 10, 9, 11, 10, 12]
const SAMPLE_2026 = [7, 9, 8, 12, 11, 14, 13, 16, 12]

const W = 640
const H = 220
const PAD_L = 34
const PAD_B = 26
const PAD_T = 14
const MAX_Y = 20

function toPoints(data: number[]) {
  const stepX = (W - PAD_L - 10) / (MONTHS.length - 1)
  return data.map((v, i) => [PAD_L + i * stepX, PAD_T + (H - PAD_T - PAD_B) * (1 - v / MAX_Y)] as const)
}

export default function TrendChart() {
  const prev = toPoints(SAMPLE_2025)
  const curr = toPoints(SAMPLE_2026)
  const line = (pts: readonly (readonly [number, number])[]) => pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${y}`).join(' ')
  const area = `${line(curr)} L${curr[curr.length - 1][0]},${H - PAD_B} L${curr[0][0]},${H - PAD_B} Z`
  const last = curr[curr.length - 1]

  return (
    <div className="rise rise-3 h-full bg-surface border border-line rounded-xl px-7 py-5">
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-bold text-strong">매칭 추이</h3>
        <div className="flex items-center gap-4 text-xs text-muted2">
          <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-dashed border-faint" />2025</span>
          <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-primary2" />2026</span>
        </div>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full mt-3" role="img" aria-label="월별 키워드 매칭 건수 추이">
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#315CFF" stopOpacity="0.14" />
            <stop offset="100%" stopColor="#315CFF" stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* 그리드 */}
        {[0, 5, 10, 15, 20].map(v => {
          const y = PAD_T + (H - PAD_T - PAD_B) * (1 - v / MAX_Y)
          return (
            <g key={v}>
              <line x1={PAD_L} y1={y} x2={W - 10} y2={y} stroke="rgba(16,24,40,0.05)" strokeWidth="1" />
              <text x={PAD_L - 8} y={y + 3.5} textAnchor="end" fontSize="10" fill="#98A2B3">{v}</text>
            </g>
          )
        })}
        {/* X축 라벨 */}
        {MONTHS.map((m, i) => {
          const x = PAD_L + i * ((W - PAD_L - 10) / (MONTHS.length - 1))
          return (
            <text key={m} x={x} y={H - 8} textAnchor="middle" fontSize="10" fill="#98A2B3">{m}</text>
          )
        })}
        {/* 2025 점선 */}
        <path d={line(prev)} fill="none" stroke="#CDD5DF" strokeWidth="1.5" strokeDasharray="4 4" />
        {/* 2026 영역 + 라인 */}
        <path d={area} fill="url(#trendFill)" />
        <path d={line(curr)} fill="none" stroke="#315CFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {/* 끝점 + 툴팁 */}
        <circle cx={last[0]} cy={last[1]} r="4" fill="#315CFF" stroke="#fff" strokeWidth="2" />
        <g transform={`translate(${last[0] - 34}, ${last[1] - 34})`}>
          <rect width="68" height="22" rx="6" fill="#101828" />
          <text x="34" y="14.5" textAnchor="middle" fontSize="10.5" fontWeight="600" fill="#fff">9월 {SAMPLE_2026[SAMPLE_2026.length - 1]}건</text>
        </g>
      </svg>
    </div>
  )
}
