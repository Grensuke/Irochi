import type { Alert, AlertStatus } from '@/types';
import { useAuth } from '@/context/AuthContext';
import StatusBadge from '@/components/StatusBadge/StatusBadge';
import AnalystNotes from '@/components/AnalystNotes/AnalystNotes';
import { addToast } from '@/components/Toast/Toast';
import './TriagePanel.css';

interface TriagePanelProps {
  alert: Alert;
  onStatusChange: (status: AlertStatus) => void;
  onAssign: (analyst: string) => void;
}

const ANALYSTS = ['Sarah Chen', 'Alex Morgan', 'James Wilson', 'Maria Garcia'];

export default function TriagePanel({ alert, onStatusChange, onAssign }: TriagePanelProps) {
  const { user } = useAuth();

  const handleAssignToMe = () => {
    if (user) {
      onAssign(user.displayName);
      addToast({ type: 'success', title: `Assigned to ${user.displayName}` });
    }
  };

  return (
    <div className="triage-panel">
      {/* Status */}
      <div>
        <div className="triage-panel__section-title">CURRENT STATUS</div>
        <div style={{ marginBottom: 'var(--space-3)' }}><StatusBadge status={alert.status} large /></div>
        <div className="triage-panel__actions">
          {alert.status === 'new' && (
            <button className="triage-panel__btn triage-panel__btn--primary" onClick={() => onStatusChange('acknowledged')}>ACKNOWLEDGE</button>
          )}
          {alert.status !== 'new' && (
            <button className="triage-panel__btn triage-panel__btn--secondary" onClick={() => onStatusChange('acknowledged')}>ACKNOWLEDGE</button>
          )}
          <button className="triage-panel__btn triage-panel__btn--secondary" onClick={() => onStatusChange('investigating')}>MARK INVESTIGATING</button>
          <button className="triage-panel__btn triage-panel__btn--danger" onClick={() => onStatusChange('escalated')}>ESCALATE</button>
          <button className="triage-panel__btn triage-panel__btn--ghost" onClick={() => onStatusChange('closed')}>CLOSE ALERT</button>
        </div>
      </div>

      {/* Analyst Notes */}
      <AnalystNotes notes={alert.notes || []} />

      {/* Assignment */}
      <div>
        <div className="triage-panel__section-title">ASSIGNED TO</div>
        <select
          className="triage-panel__select"
          value={alert.assigned_to || ''}
          onChange={e => onAssign(e.target.value)}
        >
          <option value="">Unassigned</option>
          {ANALYSTS.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <span className="triage-panel__assign-link" onClick={handleAssignToMe}>ASSIGN TO ME</span>
      </div>

      {/* Metadata */}
      <div>
        <div className="triage-panel__section-title">ALERT METADATA</div>
        <div className="triage-panel__meta-table">
          <div className="triage-panel__meta-row"><span className="triage-panel__meta-key">Alert ID</span><span className="triage-panel__meta-val">{alert.alert_id.slice(0, 12)}...</span></div>
          <div className="triage-panel__meta-row"><span className="triage-panel__meta-key">Detector</span><span className="triage-panel__meta-val">{alert.detector_id}</span></div>
          <div className="triage-panel__meta-row"><span className="triage-panel__meta-key">Schema Version</span><span className="triage-panel__meta-val">{alert.canonical_event?.schema_version || '1.2.0'}</span></div>
          <div className="triage-panel__meta-row"><span className="triage-panel__meta-key">Ingest Latency</span><span className="triage-panel__meta-val">{Math.floor(Math.random() * 200 + 20)}ms</span></div>
          <div className="triage-panel__meta-row"><span className="triage-panel__meta-key">Source Sensor</span><span className="triage-panel__meta-val">{alert.canonical_event?.sensor_source || 'zeek'}</span></div>
        </div>
      </div>
    </div>
  );
}
