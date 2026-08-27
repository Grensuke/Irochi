/**
 * Mock login page.
 *
 * MOCK ONLY — no real JWT, password hashing, session management, or auth API.
 * Any email with '@' succeeds after a simulated delay.
 */

import { useState } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

export function Login() {
  const { isAuthenticated, login, isLoading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  if (isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!email.trim()) { setLocalError('Email is required'); return; }
    if (!password.trim()) { setLocalError('Password is required'); return; }

    await login(email, password);
  };

  const displayError = localError ?? error;

  return (
    <div className="login-page">
      <div className="login-card animate-fade-in">
        <div className="login-header">
          <Link to="/" className="login-brand">
            <svg width="24" height="24" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="8" stroke="var(--accent-primary)" strokeWidth="1.5" fill="none" />
              <circle cx="10" cy="10" r="3" fill="var(--accent-primary)" />
              <line x1="10" y1="2" x2="10" y2="6" stroke="var(--accent-primary)" strokeWidth="1.5" />
              <line x1="10" y1="14" x2="10" y2="18" stroke="var(--accent-primary)" strokeWidth="1.5" />
              <line x1="2" y1="10" x2="6" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
              <line x1="14" y1="10" x2="18" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
            </svg>
            <span>IROCHI</span>
          </Link>
          <h1>Sign in to your account</h1>
          <p className="login-subtitle">Threat intelligence dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {displayError && (
            <div className="login-error animate-slide-in">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="8" cy="8" r="6.5"/><line x1="8" y1="5" x2="8" y2="8.5"/><line x1="8" y1="11" x2="8.01" y2="11"/>
              </svg>
              {displayError}
            </div>
          )}

          <div className="input-group">
            <label className="input-label" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              className="input"
              placeholder="analyst@organization.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              autoComplete="current-password"
            />
          </div>

          <div className="login-options">
            <label className="remember-me">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                disabled={isLoading}
              />
              <span>Remember me</span>
            </label>
          </div>

          <button type="submit" className="btn btn-primary btn-lg login-submit" disabled={isLoading}>
            {isLoading ? (
              <>
                <span className="connecting-spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                Signing in…
              </>
            ) : (
              'Sign in'
            )}
          </button>
        </form>

        <div className="login-footer">
          <span className="demo-badge">DEMO</span>
          <span>Any email with @ will authenticate</span>
        </div>
      </div>
    </div>
  );
}
