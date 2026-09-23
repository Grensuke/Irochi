import { useState, useEffect, useRef, FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import ThemeToggle from '@/components/ThemeToggle/ThemeToggle';
import './LoginPage.css';

// ─── Braille spinner frames ───
const SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

// ─── Eye icons ───
function EyeOpen() {
  return (
    <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1.5 9s3-5.5 7.5-5.5S16.5 9 16.5 9s-3 5.5-7.5 5.5S1.5 9 1.5 9z" />
      <circle cx="9" cy="9" r="2.5" />
    </svg>
  );
}

function EyeClosed() {
  return (
    <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7.58 7.58a2.5 2.5 0 0 0 3.34 3.34" />
      <path d="M3.18 3.18C1.5 4.72 1.5 9 1.5 9s3 5.5 7.5 5.5a7.46 7.46 0 0 0 3.82-1.18" />
      <path d="M14.12 12.12C15.78 10.78 16.5 9 16.5 9s-3-5.5-7.5-5.5c-.67 0-1.32.09-1.92.25" />
      <line x1="1.5" y1="1.5" x2="16.5" y2="16.5" />
    </svg>
  );
}

// ─── Hexagon background SVG ───
function HexBackground() {
  const hexagons: JSX.Element[] = [];
  const size = 30;
  const cols = 20;
  const rows = 30;

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const x = col * size * 1.75 + (row % 2 ? size * 0.875 : 0);
      const y = row * size * 1.5;
      hexagons.push(
        <polygon
          key={`${row}-${col}`}
          points={hexPoints(x, y, size * 0.45)}
          fill="none"
          stroke="currentColor"
          strokeWidth="0.5"
        />
      );
    }
  }

  return (
    <div className="login-page__bg">
      <svg xmlns="http://www.w3.org/2000/svg" style={{ color: 'var(--text-tertiary)', opacity: 0.04 }}>
        {hexagons}
      </svg>
    </div>
  );
}

function hexPoints(cx: number, cy: number, r: number): string {
  const points: string[] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    points.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
  }
  return points.join(' ');
}

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [spinnerFrame, setSpinnerFrame] = useState(0);
  const spinnerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location.state]);

  // Braille spinner animation
  useEffect(() => {
    if (loading) {
      spinnerRef.current = setInterval(() => {
        setSpinnerFrame(prev => (prev + 1) % SPINNER_FRAMES.length);
      }, 80);
    } else {
      if (spinnerRef.current) clearInterval(spinnerRef.current);
    }
    return () => {
      if (spinnerRef.current) clearInterval(spinnerRef.current);
    };
  }, [loading]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (loading) return;

    setError(null);
    setLoading(true);

    try {
      await login(username, password);
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <HexBackground />

      <div className="login-page__theme">
        <ThemeToggle />
      </div>

      <div className="login-card">
        <div className="login-card__brand">SIH·26145</div>
        <h1 className="login-card__title">Security Intelligence Hub</h1>
        <p className="login-card__subtitle">Analyst Access Portal</p>
        
        <div className="login-card__classification">
          <span className="mono" style={{ fontSize: '10px', color: 'var(--text-tertiary)', letterSpacing: '0.1em' }}>CLEARANCE:</span>
          <span className="mono" style={{ fontSize: '10px', color: 'var(--accent-primary)', marginLeft: '6px', fontWeight: 600 }}>LEVEL 4 RESTRICTED</span>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Error banner */}
          {error && (
            <div className="login-error">
              <span className="login-error__text">{error}</span>
              <button
                type="button"
                className="login-error__dismiss"
                onClick={() => setError(null)}
                aria-label="Dismiss error"
              >
                ×
              </button>
            </div>
          )}

          {/* Username field */}
          <div className="login-field">
            <label className="login-field__label" htmlFor="login-username">
              USERNAME
            </label>
            <div className="login-field__wrapper">
              <input
                id="login-username"
                className="login-field__input"
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
                required
              />
            </div>
          </div>

          {/* Password field */}
          <div className="login-field">
            <label className="login-field__label" htmlFor="login-password">
              PASSWORD
            </label>
            <div className="login-field__wrapper">
              <input
                id="login-password"
                className="login-field__input"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                style={{ paddingRight: '44px' }}
                required
              />
              <button
                type="button"
                className="login-field__toggle"
                onClick={() => setShowPassword(prev => !prev)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? <EyeClosed /> : <EyeOpen />}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="login-submit"
            disabled={loading || !username || !password}
          >
            {loading ? (
              <span className="login-submit__spinner">
                {SPINNER_FRAMES[spinnerFrame]}
              </span>
            ) : (
              'ACCESS SYSTEM'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
