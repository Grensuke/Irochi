import { Link } from 'react-router-dom';

export function AccessDenied() {
  return (
    <div className="state-message" style={{ minHeight: '60vh' }}>
      <svg viewBox="0 0 24 24" fill="none" stroke="var(--status-error)" strokeWidth="2" style={{ width: 48, height: 48, opacity: 1 }}>
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
      <span className="state-title" style={{ fontSize: '1.5rem' }}>Access Denied</span>
      <span className="state-detail" style={{ fontSize: '0.9rem' }}>You do not have permission to access this resource.</span>
      <Link to="/app" className="btn btn-ghost" style={{ marginTop: 'var(--space-4)' }}>
        Return to Dashboard
      </Link>
    </div>
  );
}
