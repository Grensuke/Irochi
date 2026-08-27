import { Link } from 'react-router-dom';

export function NotFound() {
  return (
    <div className="state-message" style={{ minHeight: '60vh' }}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 48, height: 48 }}>
        <circle cx="12" cy="12" r="10" />
        <path d="M16 16s-1.5-2-4-2-4 2-4 2" />
        <line x1="9" y1="9" x2="9.01" y2="9" />
        <line x1="15" y1="9" x2="15.01" y2="9" />
      </svg>
      <span className="state-title" style={{ fontSize: '1.5rem' }}>404</span>
      <span className="state-detail" style={{ fontSize: '0.9rem' }}>Page not found</span>
      <Link to="/app" className="btn btn-ghost" style={{ marginTop: 'var(--space-4)' }}>
        Return to Dashboard
      </Link>
    </div>
  );
}
