/**
 * AlertToast — Dramatic on-screen alert notification.
 *
 * Slides in from the top-right with a pulsing red/orange glow for
 * critical/high severity alerts. Features:
 *   - ⚠ CRITICAL ALERT / ⚠ HIGH ALERT header with animated pulse
 *   - Threat type, source/dest IPs, evidence summary
 *   - Auto-dismiss after 8s with progress bar
 *   - Click-to-dismiss
 */

import { useEffect, useState } from 'react';
import type { Toast } from '../contexts/NotificationContext';
import { useNotifications } from '../contexts/NotificationContext';
import { THREAT_TYPE_LABELS } from '../types';
import './AlertToast.css';

const TOAST_LIFETIME_MS = 8000;

export function AlertToastStack() {
  const { toasts, dismissToast } = useNotifications();

  return (
    <div className="alert-toast-stack" aria-live="assertive" role="alert">
      {toasts.map((toast, index) => (
        <AlertToastItem
          key={toast.id}
          toast={toast}
          index={index}
          onDismiss={() => dismissToast(toast.id)}
        />
      ))}
    </div>
  );
}

function AlertToastItem({
  toast,
  index,
  onDismiss,
}: {
  toast: Toast;
  index: number;
  onDismiss: () => void;
}) {
  const [exiting, setExiting] = useState(false);
  const { alert } = toast;
  const isCritical = alert.severity === 'critical';

  // Trigger exit animation before removal
  useEffect(() => {
    const exitTimer = setTimeout(() => {
      setExiting(true);
    }, TOAST_LIFETIME_MS - 400);

    return () => clearTimeout(exitTimer);
  }, []);

  const handleDismiss = () => {
    setExiting(true);
    setTimeout(onDismiss, 350);
  };

  return (
    <div
      className={`alert-toast ${alert.severity} ${exiting ? 'toast-exit' : 'toast-enter'}`}
      style={{ '--toast-index': index } as React.CSSProperties}
      onClick={handleDismiss}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleDismiss()}
    >
      {/* Severity Pulse Indicator */}
      <div className="toast-pulse-ring" />

      {/* Alert Header */}
      <div className="toast-header">
        <div className="toast-severity-badge">
          <span className="toast-alert-icon">⚠</span>
          <span className="toast-severity-text">
            {isCritical ? 'CRITICAL ALERT' : 'HIGH ALERT'}
          </span>
        </div>
        <button
          className="toast-dismiss"
          onClick={(e) => {
            e.stopPropagation();
            handleDismiss();
          }}
          aria-label="Dismiss alert"
        >
          ×
        </button>
      </div>

      {/* Alert Body */}
      <div className="toast-body">
        <div className="toast-threat-type">
          {THREAT_TYPE_LABELS[alert.threat_type] || alert.threat_type}
        </div>
        <div className="toast-meta">
          {alert.src_ip && (
            <span className="toast-ip">
              <span className="toast-ip-label">SRC</span> {alert.src_ip}
            </span>
          )}
          {alert.dst_ip && (
            <span className="toast-ip">
              <span className="toast-ip-label">DST</span> {alert.dst_ip}
            </span>
          )}
        </div>
        <p className="toast-evidence">{alert.evidence_summary}</p>
      </div>

      {/* Auto-dismiss progress bar */}
      <div className="toast-progress">
        <div className="toast-progress-bar" />
      </div>
    </div>
  );
}
