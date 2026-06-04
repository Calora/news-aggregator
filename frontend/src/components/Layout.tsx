import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: '每日日报', icon: '📅' },
  { to: '/all', label: '全部动态', icon: '📋' },
  { to: '/bookmarks', label: '我的收藏', icon: '⭐' },
  { to: '/sources', label: '数据源', icon: '⚙️' },
]

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white/90 backdrop-blur border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-5 h-12 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="font-bold text-base text-gray-900 tracking-tight">NewsDigest</span>
            <span className="text-[10px] font-medium text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded-full">AI</span>
          </div>
          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-100 text-gray-900'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-slate-50'
                  }`
                }
              >
                <span>{item.icon}</span>
                <span className="hidden sm:inline">{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-5 py-8">
        <Outlet />
      </main>
      <footer className="text-center py-4 text-xs text-gray-400">
        Copyright © 2026 Calora Sia · Licensed under Apache 2.0
      </footer>
    </div>
  )
}
