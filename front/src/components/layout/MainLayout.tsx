import { Outlet } from 'react-router-dom'
import DetailModal from '@/components/DetailModal'
import Header from './Header'
import { FavoritesProvider } from '@/contexts/FavoritesContext'
import { KeywordsProvider } from '@/contexts/KeywordsContext'

export default function MainLayout() {
  return (
    <FavoritesProvider>
      <KeywordsProvider>
        <div className="min-h-screen bg-[#f0f2f5]">
          <Header />
          <main className="pt-14 min-h-screen">
            <Outlet />
          </main>
          <DetailModal />
        </div>
      </KeywordsProvider>
    </FavoritesProvider>
  )
}
