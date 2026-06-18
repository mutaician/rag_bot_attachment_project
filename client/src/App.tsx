import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import ThemeToggle from './components/ThemeToggle'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'

function AppShell() {
  const location = useLocation()
  const onAsk = location.pathname === '/chat' || location.pathname.startsWith('/chat/')

  return (
    <div className="flex min-h-screen bg-paper text-ink">
      <aside className="sticky top-0 flex h-screen w-14 shrink-0 flex-col border-r border-line bg-surface md:w-48">
          <div className="border-b border-line px-3 py-5 md:px-5">
            <p className="font-display text-lg font-semibold leading-none tracking-tight md:text-xl">
              Index
            </p>
            <p className="mt-1 hidden font-mono text-[10px] uppercase tracking-[0.12em] text-faint md:block">
              Internal KB
            </p>
          </div>

          <nav className="flex flex-1 flex-col gap-1 p-2 md:p-3">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                [
                  'rounded-md px-3 py-2.5 text-sm transition-colors',
                  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
                  isActive
                    ? 'bg-accent-soft font-medium text-ink'
                    : 'text-muted hover:bg-paper-deep hover:text-ink',
                ].join(' ')
              }
            >
              <span className="md:hidden" aria-hidden>
                ◫
              </span>
              <span className="hidden md:inline">Library</span>
            </NavLink>
            <NavLink
              to="/chat"
              className={() =>
                [
                  'rounded-md px-3 py-2.5 text-sm transition-colors',
                  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
                  onAsk
                    ? 'bg-accent-soft font-medium text-ink'
                    : 'text-muted hover:bg-paper-deep hover:text-ink',
                ].join(' ')
              }
            >
              <span className="md:hidden" aria-hidden>
                ◎
              </span>
              <span className="hidden md:inline">Ask</span>
            </NavLink>
          </nav>

          <div className="border-t border-line p-2 md:p-3">
            <ThemeToggle />
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/chat/:conversationId" element={<Chat />} />
          </Routes>
        </main>
      </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
