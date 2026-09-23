import { useMemo } from 'react';
import type { ConnStateInfo } from '@/types';
import './ConnStateGrid.css';

interface ConnStateGridProps { states: ConnStateInfo[]; }

export default function ConnStateGrid({ states }: ConnStateGridProps) {
  const total = useMemo(() => states.reduce((s, st) => s + st.count, 0), [states]);

  return (
    <div className="conn-grid">
      <div className="conn-grid__title">CONNECTION STATES</div>
      <div className="conn-grid__grid">
        {states.map(st => (
          <div key={st.code} className="conn-tile">
            <div className="conn-tile__code">{st.code}</div>
            <div className="conn-tile__name">{st.name}</div>
            <div className="conn-tile__count" style={{ color: st.color }}>{st.count.toLocaleString()}</div>
            <div className="conn-tile__bar">
              <div className="conn-tile__bar-fill" style={{ width: `${(st.count / total) * 100}%`, backgroundColor: st.color }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
