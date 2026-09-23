import { useState, useEffect, useCallback, useRef } from 'react';
import type { ToastMessage } from '@/types';
import './Toast.css';

// ─── Toast hook ───
let globalAddToast: ((toast: Omit<ToastMessage, 'id'>) => void) | null = null;

export function addToast(toast: Omit<ToastMessage, 'id'>) {
  globalAddToast?.(toast);
}

export function useToast() {
  return { addToast };
}

// ─── Single Toast Item ───
function ToastItem({ toast, onRemove }: { toast: ToastMessage; onRemove: (id: string) => void }) {
  const duration = toast.duration || 6000;
  const [progress, setProgress] = useState(100);
  const startRef = useRef(Date.now());

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Date.now() - startRef.current;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
      if (remaining <= 0) {
        onRemove(toast.id);
      }
    }, 100);
    return () => clearInterval(interval);
  }, [toast.id, duration, onRemove]);

  return (
    <div className={`toast toast--${toast.type}`}>
      <div className="toast__bar" />
      <div className="toast__body">
        <div className="toast__content">
          <div className="toast__title">{toast.title}</div>
          {toast.message && <div className="toast__message">{toast.message}</div>}
        </div>
        <button className="toast__close" onClick={() => onRemove(toast.id)} aria-label="Dismiss">×</button>
      </div>
      <div className="toast__progress">
        <div className="toast__progress-fill" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}

// ─── Toast Container ───
export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const add = useCallback((toast: Omit<ToastMessage, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    setToasts(prev => [...prev.slice(-4), { ...toast, id }]); // max 5
  }, []);

  const remove = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  useEffect(() => {
    globalAddToast = add;
    return () => { globalAddToast = null; };
  }, [add]);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onRemove={remove} />
      ))}
    </div>
  );
}
