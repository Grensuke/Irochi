/**
 * VerticalMeniscusRail — Clean Floating Bubble Navigation Rail
 * 
 * Design Architecture:
 * - Clean vertical rail embedded seamlessly in the collapsed sidebar.
 * - Hardware-accelerated floating bubble indicator with fluid spring easing.
 * - Crisp white icons on active indicator, slate icons on inactive tabs.
 * - Hover popout tooltips and full keyboard navigation.
 */

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './VerticalMeniscusRail.css';

export interface VerticalNavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  end?: boolean;
}

export interface VerticalMeniscusRailProps {
  items: VerticalNavItem[];
  className?: string;
  onSelect?: (item: VerticalNavItem) => void;
}

export function VerticalMeniscusRail({
  items,
  className = '',
  onSelect
}: VerticalMeniscusRailProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Active item index
  const activeIndex = useMemo(() => {
    const exactIndex = items.findIndex((item) => item.to === location.pathname);
    if (exactIndex !== -1) return exactIndex;

    const prefixIndex = items.findIndex(
      (item) => item.to !== '/app' && location.pathname.startsWith(item.to)
    );
    if (prefixIndex !== -1) return prefixIndex;

    if (location.pathname === '/app') {
      const rootIndex = items.findIndex((item) => item.to === '/app');
      if (rootIndex !== -1) return rootIndex;
    }

    return 0;
  }, [items, location.pathname]);

  const [selectedIndex, setSelectedIndex] = useState(activeIndex);
  const [indicatorStyle, setIndicatorStyle] = useState<{
    top: number;
    height: number;
    opacity: number;
  }>({
    top: 0,
    height: 0,
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
        top: tabRect.top - containerRect.top,
        height: tabRect.height,
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

  return (
    <div
      ref={containerRef}
      className={`vertical-meniscus-rail ${className}`}
      role="tablist"
      aria-label="Collapsed navigation rail"
    >
      {/* Floating Active Bubble Indicator */}
      <div
        className="vertical-floating-bubble"
        style={{
          transform: `translateY(${indicatorStyle.top}px)`,
          height: `${indicatorStyle.height}px`,
          opacity: indicatorStyle.opacity
        }}
        aria-hidden="true"
      >
        <div className="vertical-bubble-shine" />
      </div>

      {/* Nav Tabs List */}
      <div className="vertical-meniscus-tabs">
        {items.map((item, index) => {
          const isActive = index === selectedIndex;
          return (
            <button
              key={item.to}
              ref={(el) => {
                tabRefs.current[index] = el;
              }}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-label={item.label}
              className={`vertical-meniscus-tab ${isActive ? 'is-active' : ''}`}
              onClick={() => handleTabClick(index)}
              title={item.label}
            >
              <span className="vertical-meniscus-tab-icon">
                {item.icon}
              </span>
              <span className="vertical-meniscus-tooltip">
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
