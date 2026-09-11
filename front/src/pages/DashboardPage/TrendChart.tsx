import { useEffect, useState } from 'react'
import { getDashboardTrend, type DashboardTrend } from '@/lib/dashboard'

const W = 640
const H = 220
const PAD_L = 34
const PAD_B = 26
const PAD_T = 14

/** y축 최대값을 4의 배수로 올림해 그리드(0/¼/½/¾/최대)가 항상 정수로 떨어지게 한다. */
function niceMaxY(rawMax: number) {
  return Math.max(4, Math.ceil(rawMax / 4) * 4)
}

function toPoints(data: number[], maxY: number) {
  const stepX = (W - PAD_L - 10) / (data.length - 1)
  return data.map((v, i) => [PAD_L + i * stepX, PAD_T + (H - PAD_T - PAD_B) * (1 - v / maxY)] as const)
}

const CHART_FRAME = 'rise rise-3 h-full bg-surface border border-line rounded-xl px-7 py-5'

export default function TrendChart() {
  const [trend, setTrend] = useState<DashboardTrend | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let cancelled = false
    getDashboardTrend()
      .then(result => { if (!cancelled) setTrend(result) })
      .catch(() => { if (!cancelled) setErrorMsg('매칭 추이를 불러오지 못했습니다.') })
    return () => { cancelled = true }
  }, [])

  if (errorMsg) {
    return (
      <div className={`${CHART_FRAME} flex items-center justify-center`}>
        <p className="text-sm text-danger">{errorMsg}</p>
      </div>
    )
  }

  if (!trend) {
    return (
      <div className={`${CHART_FRAME} flex items-center justify-center`}>
        <p className="text-sm text-muted2">매칭 추이를 불러오는 중...</p>
      </div>
    )
  }

  const [prevSeries, currSeries] = trend.series
  const maxY = niceMaxY(Math.max(1, ...trend.series.flatMap(s => s.counts)))
  const gridStep = maxY / 4
  const gridValues = [0, gridStep, gridStep * 2, gridStep * 3, maxY]

  const prev = toPoints(prevSeries.counts, maxY)
  const curr = toPoints(currSeries.counts, maxY)
  const line = (pts: readonly (readonly [number, number])[]) => pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${y}`).join(' ')
  const area = `${line(curr)} L${curr[curr.length - 1][0]},${H - PAD_B} L${curr[0][0]},${H - PAD_B} Z`

  // 마지막 값이 아니라 "이번 달"에 점을 찍는다 — curr 배열은 12월까지 0으로 채워져 있어
  // 마지막 인덱스를 그대로 쓰면 아직 오지 않은 달을 가리키게 된다.
  const curMonthIdx = Math.min(new Date().getMonth(), curr.length - 1)
  const last = curr[curMonthIdx]

  return (
    <div className={CHART_FRAME}>
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-bold text-strong">매칭 추이</h3>
        <div className="flex items-center gap-4 text-xs text-muted2">
          <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-dashed border-faint" />{prevSeries.year}</span>
          <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-primary2" />{currSeries.year}</span>
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
        {gridValues.map(v => {
          const y = PAD_T + (H - PAD_T - PAD_B) * (1 - v / maxY)
          return (
            <g key={v}>
              <line x1={PAD_L} y1={y} x2={W - 10} y2={y} stroke="rgba(16,24,40,0.05)" strokeWidth="1" />
              <text x={PAD_L - 8} y={y + 3.5} textAnchor="end" fontSize="10" fill="#98A2B3">{Math.round(v)}</text>
            </g>
          )
        })}
        {/* X축 라벨 */}
        {trend.months.map((m, i) => {
          const x = PAD_L + i * ((W - PAD_L - 10) / (trend.months.length - 1))
          return (
            <text key={m} x={x} y={H - 8} textAnchor="middle" fontSize="10" fill="#98A2B3">{m}</text>
          )
        })}
        {/* 작년 점선 */}
        <path d={line(prev)} fill="none" stroke="#CDD5DF" strokeWidth="1.5" strokeDasharray="4 4" />
        {/* 올해 영역 + 라인 */}
        <path d={area} fill="url(#trendFill)" />
        <path d={line(curr)} fill="none" stroke="#315CFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {/* 이번 달 점 + 툴팁 */}
        <circle cx={last[0]} cy={last[1]} r="4" fill="#315CFF" stroke="#fff" strokeWidth="2" />
        <g transform={`translate(${last[0] - 34}, ${last[1] - 34})`}>
          <rect width="68" height="22" rx="6" fill="#101828" />
          <text x="34" y="14.5" textAnchor="middle" fontSize="10.5" fontWeight="600" fill="#fff">{trend.months[curMonthIdx]} {currSeries.counts[curMonthIdx]}건</text>
        </g>
      </svg>
    </div>
  )
}
