import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface NarrativeData {
  what_was_observed: string;
  why_it_matters: string;
  what_to_investigate: string;
}

interface NarrativePanelProps {
  context: any; // The payload containing alert, correlated events, and progression
}

export function NarrativePanel({ context }: NarrativePanelProps) {
  const [narrative, setNarrative] = useState<NarrativeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    api.generateNarrative(context)
      .then(data => {
        if (active) {
          setNarrative(data);
          setLoading(false);
        }
      })
      .catch(err => {
        if (active) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { active = false; };
  }, [context.alert_id]); // Only re-fetch if the primary alert in the context changes (timeline scrub)

  if (loading) {
    return (
      <div className="panel" style={{ background: 'var(--surface-2)', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
        <div className="panel-header" style={{ borderBottom: '1px solid rgba(139, 92, 246, 0.1)' }}>
          <span className="panel-title" style={{ color: '#a78bfa' }}>AI Attack Story</span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>AI-generated from observed alert evidence</span>
        </div>
        <div className="panel-body">
          <div className="skeleton" style={{ height: '60px', marginBottom: '16px' }}></div>
          <div className="skeleton" style={{ height: '40px', marginBottom: '16px' }}></div>
          <div className="skeleton" style={{ height: '40px' }}></div>
        </div>
      </div>
    );
  }

  // Fallback to deterministic if error or malformed
  const displayNarrative = narrative || {
    what_was_observed: error ? `Vibhinetra detected activity. No narrative could be loaded due to error: ${error}` : "Vibhinetra detected activity. No narrative could be loaded.",
    why_it_matters: "Review the evidence panel.",
    what_to_investigate: "Review the correlated events."
  };

  return (
    <div className="panel" style={{ background: 'var(--surface-2)', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
      <div className="panel-header" style={{ borderBottom: '1px solid rgba(139, 92, 246, 0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="panel-title" style={{ color: '#a78bfa', display: 'flex', alignItems: 'center', gap: '8px' }}>
          AI Attack Story
        </span>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'var(--surface-1)', padding: '2px 6px', borderRadius: '4px' }}>
          AI-generated from observed alert evidence
        </span>
      </div>
      <div className="panel-body" style={{ color: 'var(--text)', fontSize: '0.9rem', lineHeight: 1.6 }}>
        
        <div style={{ marginBottom: '1.2rem' }}>
          <h4 style={{ margin: '0 0 0.4rem 0', fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>WHAT WAS OBSERVED</h4>
          <p style={{ margin: 0 }}>{displayNarrative.what_was_observed}</p>
        </div>

        <div style={{ marginBottom: '1.2rem' }}>
          <h4 style={{ margin: '0 0 0.4rem 0', fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>WHY IT MATTERS</h4>
          <p style={{ margin: 0 }}>{displayNarrative.why_it_matters}</p>
        </div>

        <div>
          <h4 style={{ margin: '0 0 0.4rem 0', fontSize: '0.75rem', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>WHAT TO INVESTIGATE</h4>
          <p style={{ margin: 0 }}>{displayNarrative.what_to_investigate}</p>
        </div>

      </div>
    </div>
  );
}
