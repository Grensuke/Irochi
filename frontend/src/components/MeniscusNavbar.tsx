/**
 * MeniscusNavbar — Clean, Elegant Floating Pill Navigation Dock
 * 
 * Design Architecture:
 * - Frosted glass pill container with subtle borders and ambient elevation.
 * - Hardware-accelerated floating capsule indicator with fluid spring physics.
 * - Organic liquid squish & stretch on movement.
 * - Smooth color crossfades without harsh popups or edge artifacts.
 * - Full React Router integration and keyboard accessibility.
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './MeniscusNavbar.css';

export interface MeniscusItem {
  id: string;
  to: string;
  label: string;
  icon: React.ReactNode;
  accentColor?: string;
  ambientColor?: string;
  badge?: string | number;
}

export interface MeniscusNavbarProps {
  items: MeniscusItem[];
  className?: string;
  variant?: 'floating' | 'header' | 'dock';
  onSelect?: (item: MeniscusItem) => void;
}

export function MeniscusNavbar({
  items,
  className = '',
  variant = 'header',
  onSelect
}: MeniscusNavbarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Active item index
  const activeIndex = useMemo(() => {
    const exactIndex = items.findIndex((item) => item.to === location.pathname);
    if (exactIndex !== -1) return exactIndex;

    const prefixIndex = items.findIndex(
      (item) => item.to !== '/' && item.to !== '/app' && location.pathname.startsWith(item.to)
    );
    if (prefixIndex !== -1) return prefixIndex;

    if (location.pathname === '/' || location.pathname === '/app') {
      const rootIndex = items.findIndex((item) => item.to === '/' || item.to === '/app');
      if (rootIndex !== -1) return rootIndex;
    }

    return 0;
  }, [items, location.pathname]);

  const [selectedIndex, setSelectedIndex] = useState(activeIndex);
  const [indicatorStyle, setIndicatorStyle] = useState<{
    left: number;
    width: number;
    opacity: number;
  }>({
    left: 0,
    width: 0,
    opacity: 0
  });

  // Sync external route changes
  useEffect(() => {
    setSelectedIndex(activeIndex);
  }, [activeIndex]);

  // Measure tab dimensions
  const updateIndicator = useCallback((index: number) => {
    const tabEl = tabRefs.current[index];
    const containerEl = containerRef.current;
    if (tabEl && containerEl) {
      const containerRect = containerEl.getBoundingClientRect();
      const tabRect = tabEl.getBoundingClientRect();
      setIndicatorStyle({
        left: tabRect.left - containerRect.left,
        width: tabRect.width,
        opacity: 1
      });
    }
  }, []);

  useEffect(() => {
    updateIndicator(selectedIndex);

    const handleResize = () => {
      updateIndicator(selectedIndex);
    };

    window.addEventListener('resize', handleResize);
    const observer = new ResizeObserver(() => {
      updateIndicator(selectedIndex);
    });

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      observer.disconnect();
    };
  }, [selectedIndex, updateIndicator]);

  const handleTabClick = (index: number) => {
    setSelectedIndex(index);
    updateIndicator(index);
    const item = items[index];
    if (onSelect) onSelect(item);
    if (item.to) navigate(item.to);
  };

  // Keyboard Navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const next = (selectedIndex + 1) % items.length;
      handleTabClick(next);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prev = (selectedIndex - 1 + items.length) % items.length;
      handleTabClick(prev);
    }
  };

  return (
    <div className={`meniscus-dock-wrapper meniscus-${variant} ${className}`}>
      <nav
        ref={containerRef}
        className="meniscus-dock"
        role="tablist"
        aria-label="Navigation dock"
        onKeyDown={handleKeyDown}
        tabIndex={0}
      >
        {/* Floating Active Pill Indicator with Fluid Spring Easing */}
        <div
          className="meniscus-floating-pill"
          style={{
            transform: `translateX(${indicatorStyle.left}px)`,
            width: `${indicatorStyle.width}px`,
            opacity: indicatorStyle.opacity
          }}
          aria-hidden="true"
        >
          <div className="meniscus-pill-shine" />
        </div>

        {/* Tab Items */}
        <div className="meniscus-tabs-row">
          {items.map((item, index) => {
            const isActive = index === selectedIndex;
            return (
              <button
                key={item.id || item.to}
                ref={(el) => {
                  tabRefs.current[index] = el;
                }}
                type="button"
                role="tab"
                aria-selected={isActive}
                aria-label={item.label}
                className={`meniscus-tab-btn ${isActive ? 'is-active' : ''}`}
                onClick={() => handleTabClick(index)}
              >
                <span className="meniscus-tab-icon">
                  {item.icon}
                </span>
                <span className="meniscus-tab-label">
                  {item.label}
                </span>

                {item.badge !== undefined && (
                  <span className="meniscus-tab-badge">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
