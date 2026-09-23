import { useState, useMemo, useEffect, useCallback } from 'react';
import type { Alert, Severity, ThreatType, AlertStatus } from '@/types';
import { generateAlertList } from '@/mocks/mockService';
import AlertFilters from '@/components/AlertTable/AlertFilters';
import AlertTable from '@/components/AlertTable/AlertTable';
import BulkActionsBar from '@/components/AlertTable/BulkActionsBar';
import Pagination from '@/components/AlertTable/Pagination';
import PageTransition from '@/components/PageTransition/PageTransition';
import { addToast } from '@/components/Toast/Toast';
import './AlertsPage.css';

const SORT_OPTIONS = [
  { label: 'NEWEST FIRST', field: 'created_at' as const, direction: 'desc' as const },
  { label: 'OLDEST FIRST', field: 'created_at' as const, direction: 'asc' as const },
  { label: 'SEVERITY (HIGH→LOW)', field: 'severity' as const, direction: 'desc' as const },
  { label: 'CONFIDENCE (HIGH→LOW)', field: 'confidence' as const, direction: 'desc' as const },
];

const SEV_ORDER: Record<Severity, number> = { critical: 4, high: 3, medium: 2, low: 1, info: 0 };
const PAGE_SIZE = 25;

export default function AlertsPage() {
  const [allAlerts, setAllAlerts] = useState<Alert[]>(() => generateAlertList(200));
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<Severity | 'all'>('all');
  const [threatFilter, setThreatFilter] = useState<ThreatType | 'all'>('all');
  const [sortIdx, setSortIdx] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [newAlertIds, setNewAlertIds] = useState<Set<string>>(new Set());
  const [sortColumn, setSortColumn] = useState<string | null>('created_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setAllAlerts(prev => {
        const newAlert: Alert = generateAlertList(1)[0];
        setNewAlertIds(ids => new Set([...ids, newAlert.alert_id]));
        setTimeout(() => setNewAlertIds(ids => { const next = new Set(ids); next.delete(newAlert.alert_id); return next; }), 800);
        return [newAlert, ...prev];
      });
    }, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Filter + sort
  const filtered = useMemo(() => {
    let result = [...allAlerts];

    if (search) {
      const q = search.toLowerCase();
      result = result.filter(a =>
        a.src_ip.includes(q) || a.dst_ip.includes(q) || a.alert_id.toLowerCase().includes(q)
      );
    }
    if (severityFilter !== 'all') result = result.filter(a => a.severity === severityFilter);
    if (threatFilter !== 'all') result = result.filter(a => a.threat_type === threatFilter);

    const sort = SORT_OPTIONS[sortIdx];
    const col = sortColumn || sort.field;
    const dir = sortDir;

    result.sort((a, b) => {
      let cmp = 0;
      if (col === 'created_at') cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      else if (col === 'severity') cmp = SEV_ORDER[a.severity] - SEV_ORDER[b.severity];
      else if (col === 'confidence') cmp = a.confidence - b.confidence;
      return dir === 'desc' ? -cmp : cmp;
    });

    return result;
  }, [allAlerts, search, severityFilter, threatFilter, sortIdx, sortColumn, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const pageAlerts = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const allSelected = pageAlerts.length > 0 && pageAlerts.every(a => selectedIds.has(a.alert_id));

  const handleSelect = (id: string) => {
    setSelectedIds(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });
  };

  const handleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(prev => { const n = new Set(prev); pageAlerts.forEach(a => n.delete(a.alert_id)); return n; });
    } else {
      setSelectedIds(prev => { const n = new Set(prev); pageAlerts.forEach(a => n.add(a.alert_id)); return n; });
    }
  };

  const handleStatusChange = useCallback((id: string, status: AlertStatus) => {
    setAllAlerts(prev => prev.map(a => a.alert_id === id ? { ...a, status } : a));
    addToast({ type: 'success', title: `Alert ${status}`, message: id.slice(0, 8) + '...' });
  }, []);

  const handleBulkAcknowledge = () => {
    setAllAlerts(prev => prev.map(a => selectedIds.has(a.alert_id) ? { ...a, status: 'acknowledged' as AlertStatus } : a));
    addToast({ type: 'success', title: `${selectedIds.size} alerts acknowledged` });
    setSelectedIds(new Set());
  };

  const handleBulkClose = () => {
    setAllAlerts(prev => prev.map(a => selectedIds.has(a.alert_id) ? { ...a, status: 'closed' as AlertStatus } : a));
    addToast({ type: 'info', title: `${selectedIds.size} alerts closed` });
    setSelectedIds(new Set());
  };

  const handleExport = () => {
    addToast({ type: 'info', title: 'Export started', message: 'CSV file will download shortly' });
  };

  const handleSortClick = (col: string) => {
    if (sortColumn === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(col);
      setSortDir('desc');
    }
  };

  const handleSortOptionChange = (idx: number) => {
    setSortIdx(idx);
    setSortColumn(SORT_OPTIONS[idx].field);
    setSortDir(SORT_OPTIONS[idx].direction);
  };

  return (
    <PageTransition>
      <div className="alerts-page">
        <AlertFilters
          search={search}
          onSearchChange={v => { setSearch(v); setCurrentPage(1); }}
          severityFilter={severityFilter}
          onSeverityChange={v => { setSeverityFilter(v); setCurrentPage(1); }}
          threatFilter={threatFilter}
          onThreatChange={v => { setThreatFilter(v); setCurrentPage(1); }}
          sortLabel={SORT_OPTIONS[sortIdx].label}
          onSortChange={handleSortOptionChange}
          sortOptions={SORT_OPTIONS}
          autoRefresh={autoRefresh}
          onAutoRefreshToggle={() => setAutoRefresh(p => !p)}
          onExport={handleExport}
        />

        <BulkActionsBar
          count={selectedIds.size}
          onAcknowledge={handleBulkAcknowledge}
          onClose={handleBulkClose}
          onExport={handleExport}
        />

        <AlertTable
          alerts={pageAlerts}
          selectedIds={selectedIds}
          onSelect={handleSelect}
          onSelectAll={handleSelectAll}
          allSelected={allSelected}
          newAlertIds={newAlertIds}
          onStatusChange={handleStatusChange}
          sortColumn={sortColumn}
          sortDir={sortDir}
          onSortClick={handleSortClick}
        />

        <Pagination
          currentPage={safePage}
          totalPages={totalPages}
          totalItems={filtered.length}
          pageSize={PAGE_SIZE}
          onPageChange={setCurrentPage}
        />
      </div>
    </PageTransition>
  );
}
