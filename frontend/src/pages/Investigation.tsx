import { useNavigate } from 'react-router-dom';
import { useIncidents } from '../hooks/useIncidents';
import { THREAT_TYPE_LABELS } from '../types';
import { formatDate, formatTimestamp } from '../utils/format';

export function Investigation() {
  const navigate = useNavigate();
  const { incidents, loading, error } = useIncidents();

  if (loading) {
    return (
      <div className="investigation-page p-6">
        <div className="skeleton" style={{ height: 200, borderRadius: 8 }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="investigation-page p-6">
        <div className="bg-red-500/10 border border-red-500/20 p-6 rounded-xl">
          <span className="block text-red-400 font-semibold mb-2">Failed to load incidents</span>
          <span className="block text-red-400/80">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="investigation-page p-6 max-w-7xl mx-auto space-y-6">
      <div className="bg-[#1C1C1E] border border-white/5 rounded-xl">
        <div className="p-6 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-white">Incident Investigation Queue</h2>
            <span className="px-2.5 py-0.5 rounded-full bg-white/10 text-sm font-medium text-gray-300">
              {incidents.length} Open
            </span>
          </div>
        </div>

        <div className="divide-y divide-white/5">
          {incidents.map((incident) => {
            const isAttack = incident.stage_state === 'likely_attack' || incident.stage_state === 'confirmed_attack';
            const stageColor = isAttack 
              ? 'bg-red-500/10 text-red-400 border-red-500/20'
              : 'bg-orange-500/10 text-orange-400 border-orange-500/20';

            return (
              <div key={incident.incident_id} className="p-6 hover:bg-white/[0.02] transition-colors flex items-center gap-6">
                
                {/* Risk Score */}
                <div className="flex-shrink-0 w-24 flex flex-col items-center justify-center p-3 bg-black/20 rounded-lg border border-white/5">
                  <div className="text-3xl font-bold text-white leading-none mb-1">
                    {incident.risk_score}
                  </div>
                  <div className="text-[10px] text-gray-500 uppercase font-semibold tracking-wider">
                    Risk Score
                  </div>
                </div>

                {/* Main Content */}
                <div className="flex-grow min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2.5 py-1 rounded text-xs font-semibold uppercase tracking-wider border ${stageColor}`}>
                      {incident.stage_state.replace('_', ' ')}
                    </span>
                    <span className="text-sm font-medium text-white/60 font-mono">
                      {incident.entity_key} ({incident.entity_type})
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-3">
                    {incident.distinct_threat_types.map(tt => (
                      <span key={tt} className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-xs text-gray-300">
                        {THREAT_TYPE_LABELS[tt] || tt}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-gray-500 font-mono">
                    <span>Alerts: {incident.member_alert_ids.length}</span>
                    <span>•</span>
                    <span>Last Active: {formatDate(incident.last_event_at)} {formatTimestamp(incident.last_event_at)}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex-shrink-0">
                  <button 
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
                    onClick={() => {
                      if (incident.member_alert_ids.length > 0) {
                        navigate(`/app/alerts/${incident.member_alert_ids[0]}`);
                      }
                    }}
                  >
                    Investigate
                  </button>
                </div>

              </div>
            );
          })}
          
          {incidents.length === 0 && (
            <div className="p-12 text-center text-gray-500">
              No active incidents to investigate.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
