import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Alert } from '@/types';
import SeverityBadge from '@/components/SeverityBadge/SeverityBadge';
import ThreatTypePill from '@/components/ThreatTypePill/ThreatTypePill';
import ConfidenceBar from '@/components/ConfidenceBar/ConfidenceBar';
import StatusBadge from '@/components/StatusBadge/StatusBadge';
import Tooltip from '@/components/Tooltip/Tooltip';
import ContextMenu, { type ContextMenuItem } from '@/components/ContextMenu/ContextMenu';

interface AlertTableRowProps {
  alert: Alert;
  selected: boolean;
  onSelect: (id: string) => void;
  isNew?: boolean;
  onStatusChange: (id: string, status: Alert['status']) => void;
}

function relativeTime(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 5) return 'just now';
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function AlertTableRow({ alert, selected, onSelect, isNew, onStatusChange }: AlertTableRowProps) {
  const navigate = useNavigate();
  const [ctx, setCtx] = useState<{ x: number; y: number } | null>(null);

  const isFresh = (Date.now() - new Date(alert.created_at).getTime()) < 300000;

  const menuItems: ContextMenuItem[] = [
    { label: 'View Detail', onClick: () => navigate(`/alerts/${alert.alert_id}`) },
    { label: 'Acknowledge', onClick: () => onStatusChange(alert.alert_id, 'acknowledged') },
    { label: 'Mark Investigating', onClick: () => onStatusChange(alert.alert_id, 'investigating') },
    { label: '', onClick: () => {}, divider: true },
    { label: 'Close Alert', onClick: () => onStatusChange(alert.alert_id, 'closed') },
    { label: 'Copy Alert ID', onClick: () => navigator.clipboard.writeText(alert.alert_id) },
  ];

  return (
    <>
      <tr
        className={`alert-table__row ${isNew ? 'alert-table__row--new' : ''}`}
        onClick={() => navigate(`/alerts/${alert.alert_id}`)}
        style={{ cursor: 'pointer' }}
      >
        <td className="alert-table__cell alert-table__cell--checkbox" onClick={e => e.stopPropagation()}>
          <input type="checkbox" checked={selected} onChange={() => onSelect(alert.alert_id)} />
        </td>
        <td className="alert-table__cell"><SeverityBadge severity={alert.severity} /></td>
        <td className="alert-table__cell"><ThreatTypePill type={alert.threat_type} /></td>
        <td className="alert-table__cell alert-table__cell--mono">
          {alert.flagged_src && <span style={{ color: 'var(--severity-critical)', marginRight: 4 }}>⚑</span>}
          {alert.src_ip}
        </td>
        <td className="alert-table__cell alert-table__cell--mono" style={{ color: 'var(--text-secondary)' }}>
          {alert.dst_ip}
        </td>
        <td className="alert-table__cell alert-table__cell--mono" style={{ color: 'var(--text-secondary)' }}>
          {alert.dst_port}
        </td>
        <td className="alert-table__cell"><ConfidenceBar value={alert.confidence} /></td>
        <td className="alert-table__cell"><StatusBadge status={alert.status} /></td>
        <td className="alert-table__cell">
          <Tooltip content={new Date(alert.created_at).toISOString()}>
            <span className="alert-table__cell--mono" style={{ color: isFresh ? 'var(--accent-primary)' : 'var(--text-secondary)', fontSize: '12px' }}>
              {relativeTime(alert.created_at)}
            </span>
          </Tooltip>
        </td>
        <td className="alert-table__cell alert-table__cell--actions" onClick={e => e.stopPropagation()}>
          <button
            className="alert-table__actions-btn"
            onClick={e => { e.stopPropagation(); setCtx({ x: e.clientX, y: e.clientY }); }}
            aria-label="Alert actions"
          >⋯</button>
        </td>
      </tr>
      {ctx && <ContextMenu items={menuItems} x={ctx.x} y={ctx.y} onClose={() => setCtx(null)} />}
    </>
  );
}
