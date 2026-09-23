import Skeleton from './Skeleton';

export default function DashboardSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* KPI Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 'var(--space-4)' }}>
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)' }}>
            <Skeleton width={80} height={10} style={{ marginBottom: 12 }} />
            <Skeleton width={100} height={32} variant="block" style={{ marginBottom: 8 }} />
            <Skeleton width={60} height={12} />
          </div>
        ))}
      </div>
      {/* Chart area */}
      <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)' }}>
        <Skeleton width={160} height={12} style={{ marginBottom: 20 }} />
        <Skeleton width="100%" height={280} variant="block" />
      </div>
      {/* Bottom grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
        {Array.from({ length: 2 }, (_, i) => (
          <div key={i} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)' }}>
            <Skeleton width={120} height={12} style={{ marginBottom: 16 }} />
            {Array.from({ length: 4 }, (_, j) => (
              <Skeleton key={j} width="100%" height={14} style={{ marginBottom: 10 }} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
