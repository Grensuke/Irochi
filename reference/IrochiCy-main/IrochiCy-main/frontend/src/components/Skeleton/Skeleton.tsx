import './Skeleton.css';

interface SkeletonProps { width?: string | number; height?: string | number; variant?: 'text' | 'circle' | 'block'; style?: React.CSSProperties; className?: string; }

export default function Skeleton({ width, height, variant = 'text', style, className = '' }: SkeletonProps) {
  return (
    <div
      className={`skeleton skeleton--${variant} ${className}`}
      style={{ width, height, ...style }}
    />
  );
}
