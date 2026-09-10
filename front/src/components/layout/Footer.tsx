import logoCompact from '@/assets/brand/forward-logo-compact.svg'

const GROUPS: { heading: string; links: { label: string; href: string; external?: boolean }[] }[] = [
  {
    heading: '서비스',
    links: [
      { label: '홈', href: '/' },
      { label: '대시보드', href: '/dashboard' },
      { label: '공고 검색', href: '/search' },
      { label: '마이페이지', href: '/mypage' },
    ],
  },
  {
    heading: '연동 기관',
    links: [
      { label: 'NTIS', href: 'https://www.ntis.go.kr', external: true },
      { label: 'IRIS', href: 'https://www.iris.go.kr', external: true },
      { label: 'K-Startup', href: 'https://www.k-startup.go.kr', external: true },
      { label: '나라장터', href: 'https://www.g2b.go.kr', external: true },
    ],
  },
  {
    heading: '문의',
    links: [
      { label: 'GitHub 저장소', href: 'https://github.com/rusa1212/Forward', external: true },
      { label: '데이터 출처: 공공데이터포털', href: 'https://www.data.go.kr', external: true },
    ],
  },
]

export default function Footer() {
  return (
    <footer className="bg-canvas border-t border-line mt-auto">
      <div className="max-w-[1200px] mx-auto px-8 py-10 flex flex-col md:flex-row gap-10 md:gap-20">
        <div className="space-y-3">
          <img src={logoCompact} alt="Forward — R&D Monitor" className="h-6 w-auto" />
          <p className="text-xs text-sub leading-relaxed">
            공공 R&D 과제 공고 키워드 모니터링
            <br />
            매일 09:00 자동 수집 · NTIS · 공공데이터포털 연동
          </p>
        </div>
        <div className="flex flex-wrap gap-14">
          {GROUPS.map(group => (
            <div key={group.heading} className="space-y-2.5">
              <p className="text-xs font-bold text-[#344054]">{group.heading}</p>
              <ul className="space-y-1.5">
                {group.links.map(link => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      {...(link.external ? { target: '_blank', rel: 'noreferrer' } : {})}
                      className="text-xs text-sub hover:text-strong transition-colors"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </footer>
  )
}
