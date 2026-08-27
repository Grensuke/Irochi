/**
 * useLiveAlerts — WebSocket connection for real-time alert feed.
 *
 * Handles the dummy WS protocol:
 *   backfill → backfill_complete → live
 *
 * Maintains connection state and separates backfilled vs live alerts.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { Alert, ConnectionState } from '../types';
import { AlertWebSocket } from '../services/websocket';

interface LiveAlert {
  alert: Alert;
  phase: 'backfill' | 'live';
  receivedAt: number;
}

interface UseLiveAlertsResult {
  liveAlerts: LiveAlert[];
  connectionState: ConnectionState;
  connect: () => void;
  disconnect: () => void;
}

const MAX_LIVE_ALERTS = 100;

export function useLiveAlerts(): UseLiveAlertsResult {
  const [liveAlerts, setLiveAlerts] = useState<LiveAlert[]>([]);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const wsRef = useRef<AlertWebSocket | null>(null);

  const handleAlert = useCallback((alert: Alert, phase: 'backfill' | 'live') => {
    setLiveAlerts((prev) => {
      const entry: LiveAlert = { alert, phase, receivedAt: Date.now() };
      const next = [entry, ...prev];
      return next.length > MAX_LIVE_ALERTS ? next.slice(0, MAX_LIVE_ALERTS) : next;
    });
  }, []);

  const handleStateChange = useCallback((state: ConnectionState) => {
    setConnectionState(state);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
    }
    setLiveAlerts([]);
    const ws = new AlertWebSocket(handleAlert, handleStateChange);
    wsRef.current = ws;
    ws.connect();
  }, [handleAlert, handleStateChange]);

  const disconnect = useCallback(() => {
    wsRef.current?.disconnect();
    wsRef.current = null;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.disconnect();
      wsRef.current = null;
    };
  }, [connect]);

  return { liveAlerts, connectionState, connect, disconnect };
}
