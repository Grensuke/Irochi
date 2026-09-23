/**
 * VibhinetraLogo — Official Brand Logo & Cyber Shield Emblem
 * 
 * Features:
 * - High-tech cyber dragon emblem with circuit traces and optical sensor iris.
 * - Responsive sizing ('xs' | 'sm' | 'md' | 'lg' | 'xl').
 * - Theme-adaptive styling with cybernetic glow in dark mode and clean titanium contrast in light mode.
 */

import './VibhinetraLogo.css';

export interface VibhinetraLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  showText?: boolean;
  className?: string;
  variant?: 'emblem' | 'full' | 'shield';
  glow?: boolean;
}

export function VibhinetraLogo({
  size = 'md',
  showText = false,
  className = '',
  variant = 'emblem',
  glow = true
}: VibhinetraLogoProps) {
  const pixelSize = typeof size === 'number' ? size : {
    xs: 20,
    sm: 26,
    md: 34,
    lg: 48,
    xl: 64
  }[size] || 34;

  return (
    <div className={`vibhinetra-brand-container vibhinetra-size-${typeof size === 'string' ? size : 'custom'} ${className}`}>
      <div 
        className={`vibhinetra-logo-badge ${glow ? 'has-glow' : ''} vibhinetra-variant-${variant}`}
        style={{
          width: `${pixelSize}px`,
          height: `${pixelSize}px`
        }}
      >
        <img 
          src="/Vibhinetra-logo.png" 
          alt="Vibhinetra Cyber Shield Logo" 
          className="vibhinetra-logo-img"
          loading="eager"
        />
        <div className="vibhinetra-logo-border" />
      </div>

      {showText && (
        <span className="vibhinetra-brand-title">
          VIBHINETRA
        </span>
      )}
    </div>
  );
}
