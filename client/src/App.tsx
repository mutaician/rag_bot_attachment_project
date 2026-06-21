import { BrowserRouter, NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import ThemeToggle from './components/ThemeToggle'
import { useAuth } from './context/AuthContext'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Login from './pages/Login'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-muted">
        Loading…
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}

function AppShell() {
  const { user, logout } = useAuth()
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

        <div className="space-y-2 border-t border-line p-2 md:p-3">
          {user && (
            <div className="hidden px-1 md:block">
              <p className="truncate text-sm font-medium text-ink">{user.display_name}</p>
              <button
                type="button"
                onClick={() => void logout()}
                className="mt-0.5 font-mono text-[10px] uppercase tracking-wide text-faint hover:text-accent"
              >
                Sign out
              </button>
            </div>
          )}
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
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
