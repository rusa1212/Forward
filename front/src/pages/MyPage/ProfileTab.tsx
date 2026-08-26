export default function ProfileTab() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 max-w-lg">
      <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-100">
        <div className="w-14 h-14 bg-[#1d3557] rounded-2xl flex items-center justify-center text-white text-xl font-bold shadow-md">김</div>
        <div>
          <h3 className="font-bold text-gray-800">김담당자</h3>
          <p className="text-sm text-gray-400">kim@company.kr</p>
        </div>
      </div>
      <div className="space-y-4">
        {[
          { label: '이름', value: '김담당자' },
          { label: '연락처', value: '010-1234-5678' },
          { label: '아이디', value: 'kim_manager' },
          { label: '사번', value: '20230001' },
          { label: '이메일', value: 'kim@company.kr' },
        ].map(item => (
          <div key={item.label} className="flex items-center py-2 border-b border-gray-50 last:border-0">
            <span className="text-xs text-gray-400 font-medium w-20 flex-shrink-0">{item.label}</span>
            <span className="text-sm text-gray-800 font-medium">{item.value}</span>
          </div>
        ))}
      </div>
      <div className="mt-6 flex gap-3">
        <button className="bg-[#1d3557] text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-[#16293f] transition-colors">정보 수정</button>
        <button className="border border-gray-200 text-gray-600 px-5 py-2 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors">비밀번호 변경</button>
      </div>
    </div>
  )
}
