import type { Alert } from '@/types';
import AlertTableRow from './AlertTableRow';
import './AlertTable.css';

interface AlertTableProps {
  alerts: Alert[];
  selectedIds: Set<string>;
  onSelect: (id: string) => void;
  onSelectAll: () => void;
  allSelected: boolean;
  newAlertIds: Set<string>;
  onStatusChange: (id: string, status: Alert['status']) => void;
  sortColumn: string | null;
  sortDir: 'asc' | 'desc';
  onSortClick: (col: string) => void;
}

function SortArrow({ col, active, dir }: { col: string; active: string | null; dir: string }) {
  if (active !== col) return null;
  return <span className="sort-arrow">{dir === 'asc' ? '▲' : '▼'}</span>;
}

export default function AlertTable({
  alerts, selectedIds, onSelect, onSelectAll, allSelected, newAlertIds, onStatusChange,
  sortColumn, sortDir, onSortClick,
}: AlertTableProps) {
  if (alerts.length === 0) {
    return (
      <div className="alert-table-wrap">
        <div className="alert-table__empty">
          <svg className="alert-table__empty-icon" width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="32" cy="32" r="28" /><circle cx="32" cy="32" r="18" /><circle cx="32" cy="32" r="8" />
            <line x1="32" y1="4" x2="32" y2="12" /><line x1="32" y1="4" x2="42" y2="22" />
          </svg>
          <div className="alert-table__empty-title">No alerts match your filters</div>
          <div className="alert-table__empty-sub">Adjust the search or severity filters to expand results</div>
        </div>
      </div>
    );
  }

  return (
    <div className="alert-table-wrap">
      <table className="alert-table">
        <thead className="alert-table__head">
          <tr>
            <th style={{ width: 40, textAlign: 'center' }}>
              <input type="checkbox" checked={allSelected} onChange={onSelectAll} style={{ accentColor: 'var(--accent-primary)', cursor: 'pointer' }} />
            </th>
            <th style={{ width: 80 }} onClick={() => onSortClick('severity')}>SEVERITY<SortArrow col="severity" active={sortColumn} dir={sortDir} /></th>
            <th style={{ width: 140 }}>THREAT TYPE</th>
            <th style={{ width: 140 }}>SOURCE IP</th>
            <th style={{ width: 140 }}>DESTINATION IP</th>
            <th style={{ width: 80 }}>PORT</th>
            <th style={{ width: 100 }} onClick={() => onSortClick('confidence')}>CONFIDENCE<SortArrow col="confidence" active={sortColumn} dir={sortDir} /></th>
            <th style={{ width: 110 }}>STATUS</th>
            <th style={{ width: 140 }} onClick={() => onSortClick('created_at')}>TIME<SortArrow col="created_at" active={sortColumn} dir={sortDir} /></th>
            <th style={{ width: 60 }}></th>
          </tr>
        </thead>
        <tbody>
          {alerts.map(alert => (
            <AlertTableRow
              key={alert.alert_id}
              alert={alert}
              selected={selectedIds.has(alert.alert_id)}
              onSelect={onSelect}
              isNew={newAlertIds.has(alert.alert_id)}
              onStatusChange={onStatusChange}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
