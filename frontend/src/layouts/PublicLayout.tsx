import { Link, Outlet, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import './PublicLayout.css';

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

  const navLinks = [
    { to: '/', label: 'Product' },
    { to: '/capabilities', label: 'Capabilities' },
    { to: '/architecture', label: 'Architecture' },
    { to: '/documentation', label: 'Documentation' },
    { to: '/about', label: 'About' },
    { to: '/contact', label: 'Contact' },
  ];

  return (
    <div className="public-layout">
      {/* Background Radial Glow */}
      <div className="public-radial-glow" />
      <div className="public-grid-texture" />

      {/* Header */}
      <header className="public-header">
        <div className="public-header-container">
          <Link to="/" className="public-brand">
            <svg width="22" height="22" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="8" stroke="var(--accent-primary)" strokeWidth="1.5" fill="none" />
              <circle cx="10" cy="10" r="3" fill="var(--accent-primary)" />
              <line x1="10" y1="2" x2="10" y2="6" stroke="var(--accent-primary)" strokeWidth="1.5" />
              <line x1="10" y1="14" x2="10" y2="18" stroke="var(--accent-primary)" strokeWidth="1.5" />
              <line x1="2" y1="10" x2="6" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
              <line x1="14" y1="10" x2="18" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
            </svg>
            <span className="public-brand-text">IROCHI</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="public-nav">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`public-nav-link ${location.pathname === link.to ? 'active' : ''}`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

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
            {navLinks.map((link) => (
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
