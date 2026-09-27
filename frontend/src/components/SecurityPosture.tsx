import { useState, useCallback } from 'react';
import { useIncidents } from '../hooks/useIncidents';
import type { DashboardSummary } from '../types';
import { THREAT_TYPE_LABELS } from '../types';
import { demoSimulator } from '../services/demoSimulator';

interface SecurityPostureProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

export function SecurityPosture({ summary, loading }: SecurityPostureProps) {
  const { incidents, loading: incidentsLoading } = useIncidents('open');
  const [isDemoRunning, setIsDemoRunning] = useState(() => demoSimulator.isRunning());

  const toggleDemoSimulator = useCallback(async () => {
    if (demoSimulator.isRunning()) {
      demoSimulator.stop();
      setIsDemoRunning(false);
    } else {
      setIsDemoRunning(true);
      await demoSimulator.start();
    }
  }, []);

  const isLoading = loading || incidentsLoading;

  let score = 100;
  let isFallback = false;

  if (incidents && incidents.length > 0) {
    const totalRisk = incidents.reduce((sum, inc) => sum + inc.risk_score, 0);
    const avgRisk = totalRisk / incidents.length;
    score = Math.max(0, Math.round(100 - avgRisk));
  } else if (summary) {
    isFallback = true;
    let penalty = 0;
    
    if (summary.by_threat_type) {
      Object.entries(summary.by_threat_type).forEach(([threatType, count]) => {
        if (count > 0) {
          // Apply a flat penalty per active threat campaign rather than penalizing every single alert
          if (threatType === 'volumetric_ddos' || threatType === 'Volumetric DDoS') {
            penalty += 5;
          } else if (threatType === 'data_exfiltration' || threatType === 'Data Exfiltration') {
            penalty += 20; 
          } else {
            penalty += 10;
          }
        }
      });
    }
    
    score = Math.max(0, 100 - penalty);
  }

  if (isLoading) {
    return (
      <div className="dashboard-kpi" style={{ marginBottom: 'var(--space-4)' }}>
        <div className="kpi-cell">
          <div className="skeleton" style={{ width: 120, height: 16, marginBottom: 8 }} />
          <div className="skeleton" style={{ width: 80, height: 36 }} />
        </div>
      </div>
    );
  }

  // Get breakdown from summary
  const threatTypes = summary?.by_threat_type || {};
  const breakdown = Object.entries(threatTypes)
    .filter(([_, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  return (
    <div className="dashboard-kpi" style={{ marginBottom: 'var(--space-4)' }}>
      <div className="kpi-grid" style={{ gridTemplateColumns: '1fr' }}>
        <div className="kpi-cell" style={{ display: 'flex', flexDirection: 'column', gap: '8px', position: 'relative', minHeight: '140px' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="kpi-label" style={{ fontSize: '14px' }}>Security Posture Score</span>
            {isFallback && <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>FALLBACK (ALERTS ONLY)</span>}
          </div>
          
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
            <span className="kpi-value" style={{ 
              fontSize: '36px', 
              color: score < 50 ? 'var(--severity-critical)' : score < 80 ? 'var(--severity-high)' : 'var(--status-success)',
              lineHeight: 1.1
            }}>
              {score}
            </span>
            <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ 100</span>
          </div>

          {breakdown.length > 0 && (
            <div style={{ marginTop: '8px', paddingTop: '12px', borderTop: '1px solid var(--border)', maxWidth: '60%' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', display: 'block' }}>
                Active Threat Categories
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {breakdown.map(([tt, count]) => (
                  <div key={tt} style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'var(--surface-3)', padding: '2px 6px', borderRadius: '4px', fontSize: '11px' }}>
                    <span style={{ color: 'var(--text-primary)' }}>{THREAT_TYPE_LABELS[tt as keyof typeof THREAT_TYPE_LABELS] || tt}</span>
                    <span style={{ color: 'var(--text-muted)' }}>({count})</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Absolutely positioned Button Box to prevent any vertical layout disruption */}
          <div style={{ position: 'absolute', top: '16px', right: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', background: 'var(--bg-panel)', padding: '12px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', width: '280px', zIndex: 10 }}>
            <button 
              onClick={toggleDemoSimulator}
              className={`btn ${isDemoRunning ? 'btn-danger' : 'btn-primary'}`}
              style={{ fontSize: '14px', padding: '10px 20px', fontWeight: 600, minWidth: '180px', height: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', letterSpacing: '0.5px' }}
            >
              {isDemoRunning ? '■ Stop Live Stream' : '▶ Play Live Stream'}
            </button>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                Replaying captured traffic from an active network dataset to demonstrate detection pipeline. (Not fake/mock data).
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
