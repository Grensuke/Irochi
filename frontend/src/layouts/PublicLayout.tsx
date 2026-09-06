import { Link, Outlet, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { MeniscusNavbar } from '../components/MeniscusNavbar';
import type { MeniscusItem } from '../components/MeniscusNavbar';
import { IrochiLogo } from '../components/IrochiLogo';
import './PublicLayout.css';

const PUBLIC_NAV_ITEMS: MeniscusItem[] = [
  {
    id: 'product',
    to: '/',
    label: 'Product',
    accentColor: '#f8fafc',
    ambientColor: 'rgba(255, 255, 255, 0.14)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    )
  },
  {
    id: 'capabilities',
    to: '/capabilities',
    label: 'Capabilities',
    accentColor: '#e2e8f0',
    ambientColor: 'rgba(255, 255, 255, 0.12)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <path d="m9 12 2 2 4-4" />
      </svg>
    )
  },
  {
    id: 'architecture',
    to: '/architecture',
    label: 'Architecture',
    accentColor: '#cbd5e1',
    ambientColor: 'rgba(255, 255, 255, 0.12)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="2" />
        <rect x="9" y="9" width="6" height="6" />
        <line x1="9" y1="1" x2="9" y2="4" />
        <line x1="15" y1="1" x2="15" y2="4" />
        <line x1="9" y1="20" x2="9" y2="23" />
        <line x1="15" y1="20" x2="15" y2="23" />
        <line x1="20" y1="9" x2="23" y2="9" />
        <line x1="20" y1="14" x2="23" y2="14" />
        <line x1="1" y1="9" x2="4" y2="9" />
        <line x1="1" y1="14" x2="4" y2="14" />
      </svg>
    )
  },
  {
    id: 'documentation',
    to: '/documentation',
    label: 'Docs',
    accentColor: '#94a3b8',
    ambientColor: 'rgba(255, 255, 255, 0.10)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      </svg>
    )
  },
  {
    id: 'about',
    to: '/about',
    label: 'About',
    accentColor: '#cbd5e1',
    ambientColor: 'rgba(255, 255, 255, 0.10)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16v-4" />
        <path d="M12 8h.01" />
      </svg>
    )
  },
  {
    id: 'contact',
    to: '/contact',
    label: 'Messages',
    accentColor: '#f8fafc',
    ambientColor: 'rgba(255, 255, 255, 0.15)',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    )
  }
];

export function PublicLayout() {
  const location = useLocation();
  const { theme, setTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    let elements: NodeListOf<Element> = document.querySelectorAll('.scroll-reveal');
    let observer: IntersectionObserver | null = null;

    const timer = setTimeout(() => {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('revealed');
            }
          });
        },
        { threshold: 0.05, rootMargin: '0px 0px -40px 0px' }
      );

      elements = document.querySelectorAll('.scroll-reveal');
      elements.forEach((el) => observer?.observe(el));
    }, 100);

    return () => {
      clearTimeout(timer);
      if (observer) {
        elements.forEach((el) => observer?.unobserve(el));
      }
    };
  }, [location.pathname]);

  return (
    <div className="public-layout">
      {/* Background Radial Glow */}
      <div className="public-radial-glow" />
      <div className="public-grid-texture" />

      {/* Header */}
      <header className="public-header">
        <div className="public-header-container">
          <Link to="/" className="public-brand">
            <IrochiLogo size={32} showText />
          </Link>

          {/* Desktop Meniscus Nav */}
          <div className="public-meniscus-nav-container">
            <MeniscusNavbar items={PUBLIC_NAV_ITEMS} variant="header" />
          </div>

          <div className="public-header-actions">
            <button 
              className="theme-switcher-btn public-theme-btn"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              aria-label="Toggle visual theme"
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
            >
              {theme === 'dark' ? 'Light mode' : 'Dark mode'}
            </button>
            <Link to="/login" className="btn btn-primary btn-sm">
              Open dashboard
            </Link>
            <button
              className="public-mobile-trigger"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle mobile menu"
            >
              <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                {mobileMenuOpen ? (
                  <path d="M4 4l12 12M4 16L16 4" />
                ) : (
                  <path d="M2 5h16M2 10h16M2 15h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="public-mobile-menu">
            {PUBLIC_NAV_ITEMS.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`public-mobile-link ${location.pathname === link.to ? 'active' : ''}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <Link
              to="/login"
              className="btn btn-primary btn-md"
              style={{ marginTop: 'var(--space-4)', width: '100%' }}
              onClick={() => setMobileMenuOpen(false)}
            >
              Open dashboard
            </Link>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="public-main-content">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="public-footer">
        <div className="public-footer-container">
          <div className="public-footer-left">
            <span className="public-footer-brand">IROCHI</span>
            <span className="public-footer-tagline">Passive by design. Evidence-driven intelligence.</span>
          </div>
          <div className="public-footer-right">
            <span>SIH26145 — Unidirectional network cyber threat detection</span>
            <span className="public-footer-copy">© 2026 Irochi. Observational Security Operations.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
