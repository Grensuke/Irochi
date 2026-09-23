import { useMemo } from 'react';
import type { TopSourceIP } from '@/types';
import './TopSourceIPs.css';

interface TopSourceIPsProps {
  data: TopSourceIP[];
}

// Country code → flag emoji
function countryFlag(code: string): string {
  try {
    return code
      .toUpperCase()
      .split('')
      .map(c => String.fromCodePoint(0x1f1e6 + c.charCodeAt(0) - 65))
      .join('');
  } catch {
    return '🌐';
  }
}

export default function TopSourceIPs({ data }: TopSourceIPsProps) {
  const maxCount = useMemo(() => Math.max(...data.map(d => d.eventCount), 1), [data]);

  return (
    <div className="top-source-ips">
      <div className="top-source-ips__title">TOP SOURCE IPs</div>
      <div className="top-source-ips__list">
        {data.map(item => (
          <div key={item.ip} className="ip-row">
            <span className="ip-row__rank">{item.rank}</span>
            <span className="ip-row__flag">{countryFlag(item.countryCode)}</span>
            <span className="ip-row__ip">{item.ip}</span>
            <div className="ip-row__bar-container">
              <div
                className="ip-row__bar"
                style={{ width: `${(item.eventCount / maxCount) * 100}%` }}
              />
            </div>
            <span className="ip-row__count">{item.eventCount.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
