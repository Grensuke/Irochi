import { useState, useEffect } from 'react';
import type { WebSocketStatus } from '@/types';
import './ConnectionLostBanner.css';

interface ConnectionLostBannerProps { wsStatus: WebSocketStatus; }

export default function ConnectionLostBanner({ wsStatus }: ConnectionLostBannerProps) {
  const [showBanner, setShowBanner] = useState(false);
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    if (wsStatus === 'offline' || wsStatus === 'reconnecting') {
      timer = setTimeout(() => setShowBanner(true), 30000);
      setAttempts(prev => prev + 1);
    } else {
      setShowBanner(false);
      setAttempts(0);
    }
    return () => { if (timer) clearTimeout(timer); };
  }, [wsStatus]);

  if (!showBanner) return null;

  return (
    <div className="conn-lost" role="alert">
      <span>⚠ Connection to pipeline lost — alerts may be delayed. Attempting to reconnect...</span>
      <span className="conn-lost__counter">Attempt {attempts} of ∞</span>
    </div>
  );
}
