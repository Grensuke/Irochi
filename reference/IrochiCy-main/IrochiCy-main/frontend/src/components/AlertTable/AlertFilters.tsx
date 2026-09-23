import { useState, useRef, useEffect } from 'react';
import type { Severity, ThreatType } from '@/types';
import './AlertFilters.css';

interface AlertFiltersProps {
  search: string;
  onSearchChange: (v: string) => void;
  severityFilter: Severity | 'all';
  onSeverityChange: (v: Severity | 'all') => void;
  threatFilter: ThreatType | 'all';
  onThreatChange: (v: ThreatType | 'all') => void;
  sortLabel: string;
  onSortChange: (idx: number) => void;
  sortOptions: { label: string }[];
  autoRefresh: boolean;
  onAutoRefreshToggle: () => void;
  onExport: () => void;
}

const SEV_PILLS: { value: Severity | 'all'; label: string; color?: string }[] = [
  { value: 'all', label: 'ALL' },
  { value: 'critical', label: 'CRITICAL', color: 'var(--severity-critical)' },
  { value: 'high', label: 'HIGH', color: 'var(--severity-high)' },
  { value: 'medium', label: 'MEDIUM', color: 'var(--severity-medium)' },
  { value: 'low', label: 'LOW', color: 'var(--severity-low)' },
];

const THREAT_OPTIONS: { value: ThreatType | 'all'; label: string; color?: string }[] = [
  { value: 'all', label: 'All Threats' },
  { value: 'ddos', label: 'DDoS', color: '#FF3B5C' },
  { value: 'recon', label: 'Reconnaissance', color: '#FF7A2F' },
  { value: 'dns', label: 'DNS/DGA', color: '#A78BFA' },
  { value: 'tls', label: 'TLS-C2', color: '#5B8CFF' },
  { value: 'exfil', label: 'Exfiltration', color: '#F5C518' },
];

export default function AlertFilters(props: AlertFiltersProps) {
  const [threatOpen, setThreatOpen] = useState(false);
  const [sortOpen, setSortOpen] = useState(false);
  const threatRef = useRef<HTMLDivElement>(null);
  const sortRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (threatRef.current && !threatRef.current.contains(e.target as Node)) setThreatOpen(false);
      if (sortRef.current && !sortRef.current.contains(e.target as Node)) setSortOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ESC clears search
  const handleSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') props.onSearchChange('');
  };

  const currentThreat = THREAT_OPTIONS.find(t => t.value === props.threatFilter) || THREAT_OPTIONS[0];

  return (
    <div className="alert-filters">
      <div className="alert-filters__left">
        {/* Search */}
        <div className="alert-filters__search">
          <svg className="alert-filters__search-icon" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.3"><circle cx="6" cy="6" r="4.5" /><line x1="9.5" y1="9.5" x2="13" y2="13" /></svg>
          <input
            className="alert-filters__search-input"
            type="text"
            placeholder="Search IPs, domains, alert IDs..."
            value={props.search}
            onChange={e => props.onSearchChange(e.target.value)}
            onKeyDown={handleSearchKey}
          />
        </div>

        {/* Severity pills */}
        <div className="alert-filters__pills">
          {SEV_PILLS.map(pill => {
            const active = props.severityFilter === pill.value;
            return (
              <button
                key={pill.value}
                className={`alert-filters__pill ${active ? 'alert-filters__pill--active' : ''}`}
                style={active && pill.color ? {
                  background: `${pill.color}15`,
                  borderColor: pill.color,
                  color: pill.color,
                } : undefined}
                onClick={() => props.onSeverityChange(pill.value)}
              >
                {pill.label}
              </button>
            );
          })}
        </div>

        {/* Threat type dropdown */}
        <div className="alert-filters__dropdown" ref={threatRef}>
          <button className="alert-filters__dropdown-trigger" onClick={() => setThreatOpen(!threatOpen)}>
            {currentThreat.label.toUpperCase()} ▾
          </button>
          {threatOpen && (
            <div className="alert-filters__dropdown-panel">
              {THREAT_OPTIONS.map(opt => (
                <div
                  key={opt.value}
                  className={`alert-filters__dropdown-option ${props.threatFilter === opt.value ? 'alert-filters__dropdown-option--active' : ''}`}
                  onClick={() => { props.onThreatChange(opt.value); setThreatOpen(false); }}
                >
                  {opt.color && <span className="alert-filters__dropdown-dot" style={{ backgroundColor: opt.color }} />}
                  {opt.label}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="alert-filters__right">
        {/* Sort dropdown */}
        <div className="alert-filters__dropdown" ref={sortRef}>
          <button className="alert-filters__dropdown-trigger" onClick={() => setSortOpen(!sortOpen)}>
            {props.sortLabel} ▾
          </button>
          {sortOpen && (
            <div className="alert-filters__dropdown-panel">
              {props.sortOptions.map((opt, idx) => (
                <div
                  key={idx}
                  className={`alert-filters__dropdown-option ${props.sortLabel === opt.label ? 'alert-filters__dropdown-option--active' : ''}`}
                  onClick={() => { props.onSortChange(idx); setSortOpen(false); }}
                >
                  {opt.label}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Auto-refresh toggle */}
        <div className="alert-filters__toggle">
          <span className="alert-filters__toggle-label">AUTO-REFRESH</span>
          <div
            className={`alert-filters__switch ${props.autoRefresh ? 'alert-filters__switch--on' : ''}`}
            onClick={props.onAutoRefreshToggle}
            role="switch"
            aria-checked={props.autoRefresh}
          >
            <div className="alert-filters__switch-thumb" />
          </div>
        </div>

        {/* Export */}
        <button className="alert-filters__export" onClick={props.onExport}>EXPORT CSV</button>
      </div>
    </div>
  );
}
