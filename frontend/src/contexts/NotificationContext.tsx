/**
 * NotificationContext — Global notification store for critical & high alerts.
 *
 * Captures incoming live alerts from `useLiveAlerts`, filters for
 * critical/high severity, and exposes:
 *   - notifications[]  — persisted list for the bell dropdown
 *   - toasts[]         — transient on-screen alert popups
 *   - unreadCount      — badge counter
 *   - markAllRead()    — clears unread flag
 *   - dismissToast()   — removes a single toast
 *   - clearAll()       — empties the notification store
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
} from 'react';
import type { ReactNode } from 'react';
import type { Alert, Severity } from '../types';

// ── Types ──────────────────────────────────────────────────
export interface Notification {
  id: string;
  alert: Alert;
  receivedAt: number;
  read: boolean;
}

export interface Toast {
  id: string;
  alert: Alert;
  createdAt: number;
}

interface NotificationContextValue {
  notifications: Notification[];
  toasts: Toast[];
  unreadCount: number;
  markAllRead: () => void;
  markRead: (id: string) => void;
  dismissToast: (id: string) => void;
  clearAll: () => void;
  /** Called internally by AppLayout to feed live alerts into the system */
  ingestAlert: (alert: Alert, phase: 'backfill' | 'live') => void;
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

// ── Constants ──────────────────────────────────────────────
const MAX_NOTIFICATIONS = 50;
const TOAST_LIFETIME_MS = 8000;
const CRITICAL_HIGH: Severity[] = ['critical', 'high'];

// ── Provider ───────────────────────────────────────────────
export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const seenRef = useRef<Set<string>>(new Set());

  // Auto-dismiss toasts after lifetime
  useEffect(() => {
    if (toasts.length === 0) return;

    const timers = toasts.map((toast) => {
      const remaining = toast.createdAt + TOAST_LIFETIME_MS - Date.now();
      if (remaining <= 0) return null;
      return setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, remaining);
    });

    return () => {
      timers.forEach((t) => t && clearTimeout(t));
    };
  }, [toasts]);

  const ingestAlert = useCallback(
    (alert: Alert, phase: 'backfill' | 'live') => {
      // Only critical & high severity
      if (!CRITICAL_HIGH.includes(alert.severity)) return;
      // De-duplicate
      if (seenRef.current.has(alert.alert_id)) return;
      seenRef.current.add(alert.alert_id);

      const now = Date.now();

      // Always add to notification bell
      const notif: Notification = {
        id: `notif-${alert.alert_id}`,
        alert,
        receivedAt: now,
        read: false,
      };
      setNotifications((prev) => {
        const next = [notif, ...prev];
        return next.length > MAX_NOTIFICATIONS
          ? next.slice(0, MAX_NOTIFICATIONS)
          : next;
      });

      // Only show toast for LIVE alerts (not backfill)
      if (phase === 'live') {
        const toast: Toast = {
          id: `toast-${alert.alert_id}-${now}`,
          alert,
          createdAt: now,
        };
        setToasts((prev) => [toast, ...prev].slice(0, 5));
      }
    },
    [],
  );

  const markAllRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const markRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    );
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
    seenRef.current.clear();
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        toasts,
        unreadCount,
        markAllRead,
        markRead,
        dismissToast,
        clearAll,
        ingestAlert,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx)
    throw new Error('useNotifications must be inside NotificationProvider');
  return ctx;
}
