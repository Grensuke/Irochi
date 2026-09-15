import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Incident } from '../types';

interface UseIncidentsResult {
  incidents: Incident[];
  total: number;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useIncidents(status?: string): UseIncidentsResult {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getIncidents(status);
      setIncidents(data.incidents || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch incidents');
      setIncidents([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, [status]);

  return { incidents, total, loading, error, refresh: fetchIncidents };
}
