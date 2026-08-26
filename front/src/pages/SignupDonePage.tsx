import { useNavigate } from 'react-router-dom'

export default function SignupDonePage() {
  const navigate = useNavigate()
  const onGoLogin = () => navigate('/login', { replace: true })

  return (
    <div className="min-h-screen bg-[#f0f2f5] flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg w-[380px] p-10 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-5">
          <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-gray-800 mb-2">회원가입 완료!</h2>
        <p className="text-sm text-gray-500 mb-8">SMS Notice 서비스에 오신 것을 환영합니다.</p>
        <button onClick={onGoLogin} className="w-full bg-[#1d3557] text-white rounded-xl py-2.5 text-sm font-semibold hover:bg-[#16293f] transition-colors">
          로그인하러 가기
        </button>
      </div>
    </div>
  )
}
