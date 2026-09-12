import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { isAuthenticated } from '@/lib/auth'
import { listAnnouncements } from '@/lib/announcements'
import StatusBadge from '@/components/common/StatusBadge'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'
import type { Announcement } from '@/types'
import heroCampus from '@/assets/landing/hero-campus.jpg'
import featResearch from '@/assets/landing/editorial-research.jpg'
import featEmail from '@/assets/landing/feature-email.jpg'
import featTeam from '@/assets/landing/feature-team.jpg'

const POPULAR = ['디지털트윈', 'AI 반도체', '스마트팩토리', '탄소중립', '바이오헬스']

const FEATURES = [
  { image: featResearch, title: '키워드 자동 매칭', desc: '구독 키워드를 등록하면 매일 09:00, 흩어져 있는 공공 R&D 공고에서 관련 과제를 자동으로 찾아 모아드립니다.' },
  { image: featEmail, title: '이메일 알림', desc: '새 공고가 키워드에 매칭되면 이메일로 알려드립니다. 마감이 다가오는 저장 공고도 놓치지 않도록 리마인드합니다.' },
  { image: featTeam, title: '팀 단위 모니터링', desc: '사원 명부 기반 계정으로 팀 전체가 같은 기준으로 공고를 모니터링하고, 관리자는 명부와 계정을 한곳에서 관리합니다.' },
]

export default function LandingPage() {
  const navigate = useNavigate()
  const [recent, setRecent] = useState<Announcement[]>([])
  const [featIdx, setFeatIdx] = useState(0)
  const [keyword, setKeyword] = useState('')

  const goSearch = (q?: string) => {
    const query = (q ?? keyword).trim()
    if (!isAuthenticated()) {
      navigate('/login')
      return
    }
    navigate(query ? `/search?q=${encodeURIComponent(query)}` : '/search')
  }

  // 비로그인 상태에서 API가 막혀 있으면 섹션을 조용히 숨긴다
  useEffect(() => {
    let cancelled = false
    listAnnouncements({ sort: 'latest', page: 1, pageSize: 5 })
      .then(({ items }) => { if (!cancelled) setRecent(items) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [])

  return (
    <div className="min-h-screen bg-white text-body flex flex-col">
      <Header />

      {/* ===== Hero ===== */}
      <section className="relative overflow-hidden">
        {/* 하단 54% 영역 — 텍스트 방향으로 페이드되는 연구단지 사진 */}
        <div
          className="absolute inset-x-0 bottom-0 h-[54%] bg-cover bg-center pointer-events-none"
          style={{
            backgroundImage: `url(${heroCampus})`,
            opacity: 0.9,
            filter: 'saturate(0.92)',
            maskImage: 'linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.4) 40%, rgba(0,0,0,1) 78%)',
            WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.4) 40%, rgba(0,0,0,1) 78%)',
          }}
        />
        <div className="relative max-w-[1200px] mx-auto px-8 pt-20 pb-44 flex flex-col items-center text-center">
          <p className="rise rise-1 text-[13px] font-bold text-primary2 tracking-wide">공공 R&D 공고 키워드 모니터링</p>
          <h1 className="rise rise-1 mt-3 text-[38px] font-extrabold text-strong leading-[1.25] tracking-[-0.5px]">
            흩어져 있는 R&D 공고,
            <br />
            키워드 하나로 모아 보세요
          </h1>
          <p className="rise rise-2 mt-4 text-base text-body">
            NTIS · 공공데이터포털의 R&D 과제 공고를 매일 자동 수집하고, 구독 키워드에 맞는 공고만 골라 알려드립니다.
          </p>

          {/* 검색바 — 유일한 플로팅 요소 */}
          <div className="rise rise-3 mt-9 w-full max-w-[820px] h-[68px] bg-white border-[1.5px] border-line rounded-[14px] shadow-float flex items-center gap-3 pl-6 pr-[7px]">
            <Search className="w-5 h-5 text-muted2 shrink-0" strokeWidth={2} />
            <input
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && goSearch()}
              placeholder="사업명, 기관명, 기술 분야, 키워드 검색"
              className="flex-1 min-w-0 bg-transparent text-[15px] text-strong placeholder:text-muted2 focus:outline-none"
            />
            <button
              onClick={() => goSearch()}
              className="pressable h-[54px] px-7 rounded-[10px] bg-primary2 hover:bg-primary-hover active:bg-primary-pressed text-white text-[15px] font-bold transition-colors shrink-0"
            >
              검색
            </button>
          </div>

          <div className="rise rise-4 mt-5 flex items-center gap-4 text-[13px]">
            <span className="text-muted2">인기 검색어</span>
            {POPULAR.map(k => (
              <button key={k} onClick={() => goSearch(k)} className="text-sub hover:text-primary2 font-medium transition-colors">
                {k}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ===== 새로 올라온 공고 (API 접근 가능할 때만) ===== */}
      {recent.length > 0 && (
        <section className="max-w-[1200px] mx-auto w-full px-8 py-16">
          <div className="flex items-baseline justify-between mb-4">
            <h2 className="text-[22px] font-extrabold text-strong tracking-[-0.3px]">새로 올라온 공고</h2>
            <button onClick={() => goSearch()} className="text-[13px] font-medium text-primary2 hover:text-primary-hover">
              전체 보기 ›
            </button>
          </div>
          <div className="border-t-2 border-strong">
            {recent.map(a => (
              <button
                key={a.id}
                onClick={() => goSearch()}
                className="w-full grid grid-cols-[76px_minmax(0,1fr)_170px_90px_130px] items-center gap-2 px-2 py-4 border-b border-line text-left hover:bg-subtle transition-colors"
              >
                <StatusBadge status={a.status} />
                <span className="text-base font-semibold text-strong truncate pr-4">{a.title}</span>
                <span className="text-[13px] text-body truncate">{a.org}</span>
                <span className="text-xs text-muted2">{a.announcementType}</span>
                <span className="text-[13px] text-body text-right whitespace-nowrap tabular-nums">
                  ~{a.deadline}{a.dday !== null && a.dday >= 0 ? ` · D-${a.dday === 0 ? 'day' : a.dday}` : ''}
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* ===== 기능 소개 — 이미지 스택 스와이프 ===== */}
      <section className="bg-canvas border-y border-line">
        <div className="max-w-[1200px] mx-auto px-8 py-20 grid md:grid-cols-2 gap-14 items-center">
          <div className="relative h-[340px]">
            {FEATURES.map((f, i) => {
              const offset = (i - featIdx + FEATURES.length) % FEATURES.length
              return (
                <img
                  key={f.title}
                  src={f.image}
                  alt={f.title}
                  className="absolute inset-0 w-full h-full object-cover rounded-2xl border border-line transition-all duration-[450ms] ease-out"
                  style={
                    offset === 0
                      ? { transform: 'none', opacity: 1, zIndex: 3 }
                      : offset === 1
                        ? { transform: 'rotate(4deg) scale(0.94) translateX(28px)', opacity: 0.5, zIndex: 2 }
                        : { transform: 'rotate(-5deg) scale(0.94) translateX(-28px)', opacity: 0.5, zIndex: 1 }
                  }
                />
              )
            })}
          </div>
          <div>
            <p className="text-[13px] font-bold text-muted2 tabular-nums">
              {String(featIdx + 1).padStart(2, '0')} / {String(FEATURES.length).padStart(2, '0')}
            </p>
            <h3 key={`t-${featIdx}`} className="rise mt-3 text-[26px] font-extrabold text-strong tracking-[-0.3px]">
              {FEATURES[featIdx].title}
            </h3>
            <p key={`d-${featIdx}`} className="rise rise-1 mt-3 text-[15px] leading-relaxed text-body max-w-[420px]">
              {FEATURES[featIdx].desc}
            </p>
            <div className="mt-8 flex items-center gap-2.5">
              <button
                onClick={() => setFeatIdx(i => (i - 1 + FEATURES.length) % FEATURES.length)}
                aria-label="이전 기능"
                className="pressable w-[38px] h-[38px] rounded-full bg-soft text-primary2 flex items-center justify-center hover:bg-[#dde7ff] transition-colors"
              >
                <ChevronLeft className="w-4 h-4" strokeWidth={2.2} />
              </button>
              <button
                onClick={() => setFeatIdx(i => (i + 1) % FEATURES.length)}
                aria-label="다음 기능"
                className="pressable w-[38px] h-[38px] rounded-full bg-soft text-primary2 flex items-center justify-center hover:bg-[#dde7ff] transition-colors"
              >
                <ChevronRight className="w-4 h-4" strokeWidth={2.2} />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section className="max-w-[1200px] mx-auto px-8 py-24 text-center">
        <h2 className="text-[26px] font-extrabold text-strong tracking-[-0.3px]">지금 키워드를 등록해 보세요</h2>
        <p className="mt-3 text-[15px] text-body">사내 사번으로 가입하면 내일 아침부터 매칭 공고가 도착합니다.</p>
        <button
          onClick={() => navigate(isAuthenticated() ? '/dashboard' : '/signup')}
          className={cn(
            'pressable mt-8 h-12 px-8 rounded-[10px] bg-primary2 hover:bg-primary-hover active:bg-primary-pressed',
            'text-white text-[15px] font-bold transition-colors'
          )}
        >
          {isAuthenticated() ? '대시보드로 이동' : '무료로 시작하기'}
        </button>
      </section>

      <Footer />
    </div>
  )
}
