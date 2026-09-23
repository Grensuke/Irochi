import { useTheme } from '@/hooks/useTheme';
import './ThemeToggle.css';

// Phosphor-style dot-matrix screen glyph for dark mode
function DarkModeIcon() {
  return (
    <svg viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="1" y="1" width="16" height="16" rx="2" stroke="currentColor" strokeWidth="1.2" />
      <circle cx="5" cy="5" r="1" fill="currentColor" />
      <circle cx="9" cy="5" r="1" fill="currentColor" />
      <circle cx="13" cy="5" r="1" fill="currentColor" />
      <circle cx="5" cy="9" r="1" fill="currentColor" />
      <circle cx="9" cy="9" r="1" fill="currentColor" />
      <circle cx="13" cy="9" r="1" fill="currentColor" />
      <circle cx="5" cy="13" r="1" fill="currentColor" />
      <circle cx="9" cy="13" r="1" fill="currentColor" />
      <circle cx="13" cy="13" r="1" fill="currentColor" />
    </svg>
  );
}

// Clean sun icon for light mode
function LightModeIcon() {
  return (
    <svg viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="9" cy="9" r="3.5" stroke="currentColor" strokeWidth="1.2" />
      <line x1="9" y1="1" x2="9" y2="3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="9" y1="15" x2="9" y2="17" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="1" y1="9" x2="3" y2="9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="15" y1="9" x2="17" y2="9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="3.34" y1="3.34" x2="4.76" y2="4.76" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="13.24" y1="13.24" x2="14.66" y2="14.66" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="3.34" y1="14.66" x2="4.76" y2="13.24" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      <line x1="13.24" y1="4.76" x2="14.66" y2="3.34" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      className="theme-toggle"
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {theme === 'dark' ? <DarkModeIcon /> : <LightModeIcon />}
    </button>
  );
}
