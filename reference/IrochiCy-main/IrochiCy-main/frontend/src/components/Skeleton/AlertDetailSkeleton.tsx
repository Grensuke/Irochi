import Skeleton from './Skeleton';

export default function AlertDetailSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {/* Top bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--space-3) 0', borderBottom: '1px solid var(--border-subtle)' }}>
        <Skeleton width={120} height={14} />
        <Skeleton width={200} height={14} />
        <div style={{ display: 'flex', gap: 8 }}><Skeleton width={80} height={22} variant="block" /><Skeleton width={70} height={22} variant="block" /></div>
      </div>
      {/* Body */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 'var(--space-4)' }}>
        {/* Main */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {/* Overview */}
          <div style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)' }}>
            <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}><Skeleton width={80} height={24} variant="block" /><Skeleton width={160} height={20} /></div>
            <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}><Skeleton width={140} height={24} /><Skeleton width={24} height={24} /><Skeleton width={120} height={24} /><Skeleton width={80} height={22} variant="block" /></div>
            <Skeleton width={120} height={10} style={{ marginBottom: 8 }} /><Skeleton width="100%" height={16} variant="block" />
          </div>
          {/* Evidence */}
          <div style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)' }}>
            <Skeleton width={100} height={10} style={{ marginBottom: 20 }} />
            {Array.from({ length: 3 }, (_, i) => (
              <div key={i} style={{ paddingLeft: 24, marginBottom: 20 }}><Skeleton width={80} height={10} style={{ marginBottom: 4 }} /><Skeleton width={200} height={14} style={{ marginBottom: 4 }} /><Skeleton width={120} height={14} /></div>
            ))}
          </div>
        </div>
        {/* Triage panel */}
        <div style={{ background: 'var(--bg-secondary)', padding: 'var(--space-6)', borderLeft: '1px solid var(--border-default)' }}>
          <Skeleton width={100} height={10} style={{ marginBottom: 12 }} />
          <Skeleton width={80} height={24} variant="block" style={{ marginBottom: 16 }} />
          {Array.from({ length: 4 }, (_, i) => (<Skeleton key={i} width="100%" height={40} variant="block" style={{ marginBottom: 8 }} />))}
          <Skeleton width={100} height={10} style={{ marginTop: 24, marginBottom: 12 }} />
          <Skeleton width="100%" height={80} variant="block" />
        </div>
      </div>
    </div>
  );
}
