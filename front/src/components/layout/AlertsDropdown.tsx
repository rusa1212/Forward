import { useNavigate } from 'react-router-dom'

const ALERTS = [
  { title: '[신규] AI 기반 민원 자동처리 시스템 개발', time: '5분 전', keyword: 'AI', unread: true },
  { title: '[마감임박] 의료기관 정보보안 취약점 점검 서비스 D-1', time: '1시간 전', keyword: '보안', unread: true },
  { title: '[신규] 공공데이터 활용 부동산 분석 플랫폼 구축', time: '3시간 전', keyword: '데이터', unread: false },
  { title: '[신규] 스마트시티 통합플랫폼 구축 사업', time: '어제', keyword: '스마트시티', unread: false },
]

export default function AlertsDropdown({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate()

  return (
    <div className="absolute top-11 right-10 w-80 bg-white rounded-xl shadow-2xl border border-gray-100 z-50 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <span className="font-semibold text-gray-800 text-sm">알림</span>
        <button className="text-xs text-[#457b9d] hover:underline">모두 읽음</button>
      </div>
      <div className="divide-y divide-gray-50 max-h-72 overflow-y-auto">
        {ALERTS.map((a, i) => (
          <div key={i} className={`px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors ${a.unread ? 'bg-blue-50/40' : ''}`}>
            <div className="flex items-start gap-2">
              {a.unread && <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0" />}
              <div className={a.unread ? '' : 'ml-3.5'}>
                <p className="text-xs text-gray-800 font-medium leading-relaxed">{a.title}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">{a.keyword}</span>
                  <span className="text-[10px] text-gray-400">{a.time}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="px-4 py-2.5 border-t border-gray-100 text-center">
        <button onClick={() => { navigate('/mypage'); onClose() }} className="text-xs text-[#457b9d] hover:underline">알림 설정 보기</button>
      </div>
    </div>
  )
}
