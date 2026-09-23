import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { Alert, AlertStatus } from '@/types';
import { generateMockAlert, generateRelatedAlerts } from '@/mocks/mockService';
import SeverityBadge from '@/components/SeverityBadge/SeverityBadge';
import StatusBadge from '@/components/StatusBadge/StatusBadge';
import AlertOverviewCard from '@/components/AlertOverviewCard/AlertOverviewCard';
import EvidenceTimeline from '@/components/EvidenceTimeline/EvidenceTimeline';
import RawEventViewer from '@/components/RawEventViewer/RawEventViewer';
import RelatedAlerts from '@/components/RelatedAlerts/RelatedAlerts';
import TriagePanel from '@/components/TriagePanel/TriagePanel';
import PageTransition from '@/components/PageTransition/PageTransition';
import { addToast } from '@/components/Toast/Toast';
import './AlertDetailPage.css';

export default function AlertDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Generate a deterministic mock alert based on the ID
  const [alert, setAlert] = useState<Alert>(() =>
    generateMockAlert({ alert_id: id || 'demo-alert-001' })
  );

  const relatedAlerts = useMemo(
    () => generateRelatedAlerts(alert.src_ip, alert.alert_id),
    [alert.src_ip, alert.alert_id]
  );

  const handleStatusChange = (status: AlertStatus) => {
    setAlert(prev => ({ ...prev, status }));
    addToast({ type: 'success', title: `Alert ${status}`, message: `Status changed to ${status.toUpperCase()}` });
  };

  const handleAssign = (analyst: string) => {
    setAlert(prev => ({ ...prev, assigned_to: analyst || undefined }));
  };

  return (
    <PageTransition>
      <div className="alert-detail">
        {/* Top bar */}
        <div className="alert-detail__topbar">
          <span className="alert-detail__back" onClick={() => navigate('/alerts')}>
            ← Back to Alerts
          </span>
          <span className="alert-detail__id">{alert.alert_id}</span>
          <div className="alert-detail__badges">
            <SeverityBadge severity={alert.severity} large />
            <StatusBadge status={alert.status} large />
          </div>
        </div>

        {/* Two-column body */}
        <div className="alert-detail__body">
          <div className="alert-detail__main">
            <AlertOverviewCard alert={alert} />
            <EvidenceTimeline evidence={alert.evidence} threatType={alert.threat_type} />
            <RawEventViewer event={alert.canonical_event} />
            <RelatedAlerts alerts={relatedAlerts} />
          </div>
          <div className="alert-detail__aside">
            <TriagePanel
              alert={alert}
              onStatusChange={handleStatusChange}
              onAssign={handleAssign}
            />
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
