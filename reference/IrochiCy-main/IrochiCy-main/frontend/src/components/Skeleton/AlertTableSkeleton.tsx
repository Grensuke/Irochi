import Skeleton from './Skeleton';

export default function AlertTableSkeleton() {
  return (
    <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
      {/* Header row */}
      <div style={{ display: 'flex', gap: 12, padding: '12px 16px', borderBottom: '1px solid var(--border-default)' }}>
        <Skeleton width={20} height={14} />
        <Skeleton width={60} height={14} />
        <Skeleton width={80} height={14} />
        <Skeleton width={100} height={14} />
        <Skeleton width={100} height={14} />
        <Skeleton width={60} height={14} />
        <Skeleton width={80} height={14} />
        <Skeleton width={70} height={14} />
        <Skeleton width={60} height={14} />
      </div>
      {/* Data rows */}
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} style={{ display: 'flex', gap: 12, padding: '16px', borderBottom: '1px solid var(--border-subtle)', alignItems: 'center' }}>
          <Skeleton width={16} height={16} variant="circle" />
          <Skeleton width={70} height={20} variant="block" />
          <Skeleton width={80} height={22} variant="block" />
          <Skeleton width={110} height={14} />
          <Skeleton width={100} height={14} />
          <Skeleton width={40} height={14} />
          <Skeleton width={80} height={8} variant="block" />
          <Skeleton width={70} height={20} variant="block" />
          <Skeleton width={50} height={14} />
        </div>
      ))}
    </div>
  );
}
