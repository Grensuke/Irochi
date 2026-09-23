import './BulkActionsBar.css';

interface BulkActionsBarProps {
  count: number;
  onAcknowledge: () => void;
  onClose: () => void;
  onExport: () => void;
}

export default function BulkActionsBar({ count, onAcknowledge, onClose, onExport }: BulkActionsBarProps) {
  if (count === 0) return null;
  return (
    <div className="bulk-bar">
      <span className="bulk-bar__count">{count} alert{count > 1 ? 's' : ''} selected</span>
      <div className="bulk-bar__actions">
        <button className="bulk-bar__btn" onClick={onAcknowledge}>Acknowledge All</button>
        <button className="bulk-bar__btn" onClick={onClose}>Close All</button>
        <button className="bulk-bar__btn" onClick={onExport}>Export Selected</button>
      </div>
    </div>
  );
}
