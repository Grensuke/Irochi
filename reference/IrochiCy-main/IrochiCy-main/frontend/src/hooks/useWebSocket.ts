import { useState, useEffect, useCallback, useRef } from 'react';
import type { Alert, WebSocketStatus } from '@/types';
import { simulateLiveAlerts, generateInitialAlerts } from '@/mocks/mockService';

interface UseWebSocketReturn {
  status: WebSocketStatus;
  alerts: Alert[];
  latestAlert: Alert | null;
}

const IS_MOCK = import.meta.env.VITE_MOCK !== 'false';

export function useWebSocket(): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>('connecting');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [latestAlert, setLatestAlert] = useState<Alert | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  const reconnectAttemptRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);

  const handleNewAlert = useCallback((alert: Alert) => {
    setLatestAlert(alert);
    setAlerts(prev => {
      const next = [alert, ...prev];
      // Keep only last 100 alerts in memory
      return next.slice(0, 100);
    });
  }, []);

  // ─── Mock Mode ───
  useEffect(() => {
    if (!IS_MOCK) return;

    // Load initial batch
    const initial = generateInitialAlerts(20);
    setAlerts(initial);

    // Simulate connection delay
    const connectTimer = setTimeout(() => {
      setStatus('live');

      // Start generating live alerts
      cleanupRef.current = simulateLiveAlerts(handleNewAlert, [2000, 6000]);
    }, 1200);

    return () => {
      clearTimeout(connectTimer);
      if (cleanupRef.current) cleanupRef.current();
    };
  }, [handleNewAlert]);

  // ─── Production WebSocket Mode ───
  useEffect(() => {
    if (IS_MOCK) return;

    function connect() {
      setStatus('connecting');
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/alerts`);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('live');
        reconnectAttemptRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'alert') {
            handleNewAlert(data.payload as Alert);
          }
        } catch {
          console.error('Failed to parse WebSocket message');
        }
      };

      ws.onclose = () => {
        setStatus('reconnecting');
        wsRef.current = null;

        // Exponential backoff: 1s, 2s, 4s, 8s, ... max 30s
        const delay = Math.min(
          1000 * Math.pow(2, reconnectAttemptRef.current),
          30000
        );
        reconnectAttemptRef.current++;

        setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [handleNewAlert]);

  return { status, alerts, latestAlert };
}
