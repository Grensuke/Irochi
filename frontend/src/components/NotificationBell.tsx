/**
 * NotificationBell — Bell icon with badge + dropdown panel.
 *
 * Placed in the top header bar. Shows:
 *   - Bell icon with unread count badge
 *   - Click opens a dropdown panel listing recent critical/high notifications
 *   - "Mark all read" and "Clear all" actions
 *   - Each notification shows severity, threat type, time ago, and IPs
 */

import { useState, useRef, useEffect } from 'react';
import { useNotifications } from '../contexts/NotificationContext';
import { THREAT_TYPE_LABELS } from '../types';
import './NotificationBell.css';

export function NotificationBell() {
  const { notifications, unreadCount, markAllRead, markRead, clearAll } =
    useNotifications();
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleEsc);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleEsc);
    };
  }, [open]);

  const toggle = () => setOpen((prev) => !prev);

  return (
    <div className="notification-bell-container">
      <button
        ref={buttonRef}
        className={`notification-bell-btn ${unreadCount > 0 ? 'has-unread' : ''}`}
        onClick={toggle}
        aria-label={`Notifications: ${unreadCount} unread`}
        aria-expanded={open}
        title={`${unreadCount} unread notifications`}
      >
        {/* Bell icon */}
        <svg
          className="bell-icon"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          width="18"
          height="18"
        >
          <path d="M10 2.5a5 5 0 0 0-5 5v3.5L3 13.5h14L15 11V7.5a5 5 0 0 0-5-5z" />
          <path d="M8 15a2 2 0 0 0 4 0" />
        </svg>

        {/* Badge */}
        {unreadCount > 0 && (
          <span className="notification-badge">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}

        {/* Pulse ring on unread */}
        {unreadCount > 0 && <span className="bell-pulse-ring" />}
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div ref={panelRef} className="notification-panel">
          <div className="notification-panel-header">
            <h3 className="notification-panel-title">
              Notifications
              {unreadCount > 0 && (
                <span className="notification-panel-count">{unreadCount}</span>
              )}
            </h3>
            <div className="notification-panel-actions">
              {unreadCount > 0 && (
                <button
                  className="notification-action-btn"
                  onClick={() => markAllRead()}
                >
                  Mark all read
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  className="notification-action-btn danger"
                  onClick={() => clearAll()}
                >
                  Clear all
                </button>
              )}
            </div>
          </div>

          <div className="notification-panel-body">
            {notifications.length === 0 ? (
              <div className="notification-empty">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.2"
                  width="32"
                  height="32"
                >
                  <path d="M12 3a7 7 0 0 0-7 7v4L3 17h18l-2-3v-4a7 7 0 0 0-7-7z" />
                  <path d="M9.5 20a2.5 2.5 0 0 0 5 0" />
                </svg>
                <p>No notifications</p>
                <span>Critical and high severity alerts will appear here</span>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`notification-item ${notif.alert.severity} ${notif.read ? 'read' : 'unread'}`}
                  onClick={() => markRead(notif.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && markRead(notif.id)}
                >
                  {/* Severity dot */}
                  <div className="notification-severity-dot" />

                  <div className="notification-content">
                    <div className="notification-top-row">
                      <span className="notification-severity-label">
                        {notif.alert.severity === 'critical'
                          ? '⚠ CRITICAL'
                          : '⚠ HIGH'}
                      </span>
                      <span className="notification-time">
                        {getTimeAgo(notif.receivedAt)}
                      </span>
                    </div>
                    <span className="notification-threat">
                      {THREAT_TYPE_LABELS[notif.alert.threat_type] ||
                        notif.alert.threat_type}
                    </span>
                    <div className="notification-ips">
                      {notif.alert.src_ip && (
                        <code>{notif.alert.src_ip}</code>
                      )}
                      {notif.alert.src_ip && notif.alert.dst_ip && (
                        <span className="notification-arrow">→</span>
                      )}
                      {notif.alert.dst_ip && (
                        <code>{notif.alert.dst_ip}</code>
                      )}
                    </div>
                  </div>

                  {/* Unread indicator */}
                  {!notif.read && <div className="notification-unread-dot" />}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Helpers ────────────────────────────────────────────────
function getTimeAgo(timestamp: number): string {
  const diff = Date.now() - timestamp;
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
