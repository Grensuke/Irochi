import { useState, useMemo } from 'react';
import type { ThreatType, Alert } from '@/types';
import { generateMockAlert } from '@/mocks/mockService';
import ThreatSelector from '@/components/ThreatSelector/ThreatSelector';
import ThreatDetail from '@/components/ThreatDetail/ThreatDetail';
import PageTransition from '@/components/PageTransition/PageTransition';
import './ThreatsPage.css';

const TYPES: ThreatType[] = ['ddos', 'recon', 'dns', 'tls', 'exfil'];

function randInt(a: number, b: number) { return Math.floor(Math.random() * (b - a + 1)) + a; }

export default function ThreatsPage() {
  const [selected, setSelected] = useState<ThreatType>('ddos');

  const counts = useMemo<Record<ThreatType, number>>(() => ({
    ddos: randInt(30, 80), recon: randInt(15, 50), dns: randInt(20, 60), tls: randInt(5, 25), exfil: randInt(3, 18),
  }), []);

  const recentAlerts = useMemo<Record<ThreatType, Alert[]>>(() => {
    const result = {} as Record<ThreatType, Alert[]>;
    TYPES.forEach(t => {
      result[t] = Array.from({ length: 10 }, (_, i) =>
        generateMockAlert({
          threat_type: t,
          created_at: new Date(Date.now() - i * randInt(60000, 600000)).toISOString(),
        })
      );
    });
    return result;
  }, []);

  return (
    <PageTransition>
      <div className="threats-page">
        <ThreatSelector selected={selected} onSelect={setSelected} counts={counts} />
        <ThreatDetail type={selected} count={counts[selected]} recentAlerts={recentAlerts[selected]} />
      </div>
    </PageTransition>
  );
}
