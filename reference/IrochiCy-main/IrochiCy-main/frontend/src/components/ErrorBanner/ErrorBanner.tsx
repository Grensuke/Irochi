import type { ApiError } from '@/hooks/useApiError';
import './ErrorBanner.css';

interface ErrorBannerProps {
  error: ApiError;
  onRetry?: () => void;
  onDismiss: () => void;
}

export default function ErrorBanner({ error, onRetry, onDismiss }: ErrorBannerProps) {
  return (
    <div className="error-banner" role="alert">
      <svg className="error-banner__icon" width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M9 1.5L1.5 15h15L9 1.5z" /><line x1="9" y1="6.5" x2="9" y2="10" /><circle cx="9" cy="12.5" r="0.5" fill="currentColor" />
      </svg>
      <span className="error-banner__msg">{error.message}</span>
      {error.retryable && onRetry && (
        <button className="error-banner__retry" onClick={onRetry}>RETRY</button>
      )}
      <span className="error-banner__dismiss" onClick={onDismiss}>DISMISS</span>
    </div>
  );
}
