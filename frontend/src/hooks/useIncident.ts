import { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Incident } from '../types';

interface UseIncidentResult {
  incident: Incident | null;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export function useIncident(incidentId: string | null | undefined): UseIncidentResult {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState<boolean>(!!incidentId);
  const [error, setError] = useState<Error | null>(null);

  const fetchIncident = async () => {
    if (!incidentId) {
      setIncident(null);
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const data = await api.getIncident(incidentId);
      setIncident(data);
    } catch (err: any) {
      setError(err);
      setIncident(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncident();
  }, [incidentId]);

  return { incident, loading, error, refresh: fetchIncident };
}
