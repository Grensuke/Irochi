import React from 'react';
import type { Incident } from '../types';
import { THREAT_TYPE_LABELS } from '../types';
import { CheckCircle2, Circle } from 'lucide-react';

const KILL_CHAIN = [
  'recon_portscan',
  'dga_dns_tunnel',
  'c2_beaconing',
  'encrypted_malware',
  'data_exfiltration'
];

interface EvidenceChainProps {
  incident: Incident;
}

export function EvidenceChain({ incident }: EvidenceChainProps) {
  // If volumetric DDoS or Novel Anomaly, the kill chain isn't standard
  const hasStandardChain = incident.distinct_threat_types.some(tt => KILL_CHAIN.includes(tt));
  
  if (!hasStandardChain) {
    return (
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Threat Capabilities</span>
        </div>
        <div className="panel-body" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          {incident.distinct_threat_types.map(tt => (
            <div key={tt} style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--surface-2)', border: '1px solid var(--border)', padding: '12px 16px', borderRadius: '8px' }}>
              <CheckCircle2 size={20} style={{ color: 'var(--accent)' }} />
              <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text)' }}>{THREAT_TYPE_LABELS[tt] || tt}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title">Kill-Chain Progression</span>
      </div>
      <div className="panel-body" style={{ position: 'relative', padding: '32px 16px' }}>
        {/* Connecting line background */}
        <div style={{ position: 'absolute', left: '10%', right: '10%', top: '56px', height: '2px', background: 'var(--border)', zIndex: 0 }} />
        
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', position: 'relative', zIndex: 10 }}>
          {KILL_CHAIN.map((stage, idx) => {
            const isActive = incident.distinct_threat_types.includes(stage as any);
            const isCurrent = incident.current_stage === stage;
            const isForecast = incident.forecast_next_stage === stage;
            
            return (
              <div key={stage} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', flex: 1 }}>
                <div style={{ 
                  width: '48px', 
                  height: '48px', 
                  borderRadius: '50%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  border: '2px solid',
                  transition: 'all 0.2s',
                  background: isActive ? 'var(--surface-3)' : isForecast ? 'rgba(239, 68, 68, 0.1)' : 'var(--surface-1)',
                  borderColor: isActive ? 'var(--accent)' : isForecast ? 'var(--status-critical)' : 'var(--border)',
                  color: isActive ? 'var(--accent)' : isForecast ? 'var(--status-critical)' : 'var(--text-muted)',
                  borderStyle: isForecast ? 'dashed' : 'solid'
                }}>
                  {isActive ? <CheckCircle2 size={24} /> : <Circle size={24} />}
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ 
                    fontSize: '0.75rem', 
                    fontWeight: 500, 
                    maxWidth: '100px', 
                    margin: '0 auto',
                    color: isActive ? 'var(--text)' : isForecast ? 'var(--status-critical)' : 'var(--text-muted)'
                  }}>
                    {THREAT_TYPE_LABELS[stage as any] || stage}
                  </div>
                  {isCurrent && (
                    <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent)', marginTop: '4px', fontWeight: 600 }}>
                      Current
                    </div>
                  )}
                  {isForecast && (
                    <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--status-critical)', marginTop: '4px', fontWeight: 600 }}>
                      Forecast
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
