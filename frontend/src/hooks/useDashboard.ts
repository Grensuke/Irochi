/**
 * useDashboard — fetch dashboard summary from the API.
 */

import { useCallback, useEffect, useState } from 'react';
import type { DashboardSummary } from '../types';
import { api } from '../services/api';

interface UseDashboardResult {
  summary: DashboardSummary | null;
  loading: boolean;
  error: string | null;
  isMock: boolean;
  refetch: () => void;
}

export function useDashboard(): UseDashboardResult {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getDashboardSummary();
      setSummary(data);
      setIsMock(false);
    } catch (e) {
      console.warn('Dashboard API failed:', e);
      setError(e instanceof Error ? e.message : 'Failed to fetch dashboard summary');
      setIsMock(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { summary, loading, error, isMock, refetch: fetchData };
}
