import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'

/**
 * App shell — shared layout + client-side routing.
 * BrowserRouter keeps the URL in sync with the visible page (no full reload).
 */
export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <header className="border-b border-gray-800 px-6 py-4">
          <nav className="mx-auto flex max-w-4xl items-center gap-6">
            <span className="font-semibold">Knowledge Base</span>
            <NavLink
              to="/"
              className={({ isActive }) =>
                isActive ? 'text-white' : 'text-gray-400 hover:text-gray-200'
              }
            >
              Documents
            </NavLink>
            <NavLink
              to="/chat"
              className={({ isActive }) =>
                isActive ? 'text-white' : 'text-gray-400 hover:text-gray-200'
              }
            >
              Chat
            </NavLink>
          </nav>
        </header>

        <main className="mx-auto max-w-4xl px-6 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
