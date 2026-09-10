import { Outlet } from 'react-router-dom'
import DetailModal from '@/components/DetailModal'
import Header from './Header'
import Footer from './Footer'
import { FavoritesProvider } from '@/contexts/FavoritesContext'
import { KeywordsProvider } from '@/contexts/KeywordsContext'

export default function MainLayout() {
  return (
    <FavoritesProvider>
      <KeywordsProvider>
        <div className="min-h-screen bg-canvas text-body flex flex-col">
          <Header />
          <main className="flex-1">
            <Outlet />
          </main>
          <Footer />
          <DetailModal />
        </div>
      </KeywordsProvider>
    </FavoritesProvider>
  )
}
