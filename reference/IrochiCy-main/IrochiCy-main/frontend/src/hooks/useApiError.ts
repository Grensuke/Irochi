import { useState, useCallback } from 'react';

export interface ApiError {
  code: number;
  message: string;
  retryable: boolean;
}

export function useApiError() {
  const [error, setError] = useState<ApiError | null>(null);

  const handleError = useCallback((err: unknown) => {
    if (err instanceof Error) {
      const msg = err.message;
      if (msg.includes('Unauthorized') || msg.includes('401')) {
        setError({ code: 401, message: 'Session expired. Redirecting to login...', retryable: false });
      } else if (msg.includes('Access denied') || msg.includes('403')) {
        setError({ code: 403, message: 'Access denied — insufficient permissions.', retryable: false });
      } else if (msg.includes('Not found') || msg.includes('404')) {
        setError({ code: 404, message: 'Resource not found.', retryable: false });
      } else if (msg.includes('Server error') || msg.includes('5')) {
        setError({ code: 500, message: 'Server error — please try again.', retryable: true });
      } else {
        setError({ code: 0, message: msg || 'An unexpected error occurred.', retryable: true });
      }
    } else {
      setError({ code: 0, message: 'An unexpected error occurred.', retryable: true });
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);
  const dismissError = clearError;

  return { error, handleError, clearError, dismissError };
}
