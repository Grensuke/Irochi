/**
 * useAlerts — fetch all alerts from the API.
 */

import { useCallback, useEffect, useState } from 'react';
import type { Alert } from '../types';
import { api } from '../services/api';

interface UseAlertsResult {
  alerts: Alert[];
  loading: boolean;
  error: string | null;
  isMock: boolean;
  refetch: () => void;
}

export function useAlerts(): UseAlertsResult {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAlerts();
      setAlerts(data.alerts);
      setIsMock(false);
    } catch (e) {
      console.warn('Alerts API failed, using mock data:', e);
      // Fallback to mock data to prevent UI breakage
      const { MOCK_ALERTS } = await import('../services/mockData');
      setAlerts(MOCK_ALERTS);
      setIsMock(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { alerts, loading, error, isMock, refetch: fetchData };
}
