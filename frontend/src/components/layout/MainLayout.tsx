import { Outlet } from 'react-router-dom'
import { useState } from 'react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { MobileNav } from './MobileNav'
import { MobileSidebar } from './MobileSidebar'

export const MainLayout = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <Header />
      
      {/* Desktop Layout */}
      <div className="hidden md:flex h-[calc(100vh-4rem)]">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile Layout */}
      <div className="md:hidden">
        <main className="pb-16">
          <div className="p-4">
            <Outlet />
          </div>
        </main>
        <MobileNav onMenuClick={() => setMobileMenuOpen(true)} />
        <MobileSidebar 
          open={mobileMenuOpen} 
          onClose={() => setMobileMenuOpen(false)} 
        />
      </div>
    </div>
  )
}