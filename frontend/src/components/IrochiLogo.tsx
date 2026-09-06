/**
 * IrochiLogo — Official Brand Logo & Cyber Shield Emblem
 * 
 * Features:
 * - High-tech cyber dragon emblem with circuit traces and optical sensor iris.
 * - Responsive sizing ('xs' | 'sm' | 'md' | 'lg' | 'xl').
 * - Theme-adaptive styling with cybernetic glow in dark mode and clean titanium contrast in light mode.
 */

import './IrochiLogo.css';

export interface IrochiLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  showText?: boolean;
  className?: string;
  variant?: 'emblem' | 'full' | 'shield';
  glow?: boolean;
}

export function IrochiLogo({
  size = 'md',
  showText = false,
  className = '',
  variant = 'emblem',
  glow = true
}: IrochiLogoProps) {
  const pixelSize = typeof size === 'number' ? size : {
    xs: 20,
    sm: 26,
    md: 34,
    lg: 48,
    xl: 64
  }[size] || 34;

  return (
    <div className={`irochi-brand-container irochi-size-${typeof size === 'string' ? size : 'custom'} ${className}`}>
      <div 
        className={`irochi-logo-badge ${glow ? 'has-glow' : ''} irochi-variant-${variant}`}
        style={{
          width: `${pixelSize}px`,
          height: `${pixelSize}px`
        }}
      >
        <img 
          src="/irochi-logo.jpg" 
          alt="Irochi Cyber Shield Logo" 
          className="irochi-logo-img"
          loading="eager"
        />
        <div className="irochi-logo-border" />
      </div>

      {showText && (
        <span className="irochi-brand-title">
          IROCHI
        </span>
      )}
    </div>
  );
}
