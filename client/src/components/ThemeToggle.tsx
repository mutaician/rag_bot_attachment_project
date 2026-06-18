import { useTheme } from '../hooks/useTheme'

export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="flex w-full items-center gap-2 rounded-md px-3 py-2.5 text-sm text-muted transition-colors hover:bg-paper-deep hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <span className="font-mono text-base leading-none" aria-hidden>
        {isDark ? '☀' : '☾'}
      </span>
      <span className="hidden md:inline">{isDark ? 'Light' : 'Dark'}</span>
    </button>
  )
}
