/**
 * Authenticated application shell — sidebar navigation + top header.
 * 
 * Features:
 * - Collapsed sidebar transforms into a vertical Meniscus liquid navigation rail
 * - Monochrome black and grey palette with metallic silver highlights and illuminated active bead
 * - Responsive desktop sidebar & mobile drawer overlay
 */

import { NavLink, Link, Outlet, useLocation } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useLiveAlerts } from '../hooks/useLiveAlerts';
import { VerticalMeniscusRail } from '../components/VerticalMeniscusRail';
import type { VerticalNavItem } from '../components/VerticalMeniscusRail';
import { IrochiLogo } from '../components/IrochiLogo';
import './AppLayout.css';

const ICONS: Record<string, ReactNode> = {
  grid: (
    <svg viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg>
  ),
  bell: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M8 1.5a4 4 0 0 0-4 4v3l-1.5 2h11L12 8.5v-3a4 4 0 0 0-4-4z"/><path d="M6.5 13.5a1.5 1.5 0 0 0 3 0"/></svg>
  ),
  shield: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M8 1.5L2.5 4v4c0 3.5 2.5 5.5 5.5 6.5 3-1 5.5-3 5.5-6.5V4L8 1.5z"/></svg>
  ),
  network: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="8" cy="3" r="1.5"/><circle cx="3" cy="13" r="1.5"/><circle cx="13" cy="13" r="1.5"/><line x1="8" y1="4.5" x2="3" y2="11.5"/><line x1="8" y1="4.5" x2="13" y2="11.5"/></svg>
  ),
  chart: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="1" y="9" width="3" height="5.5" rx="0.5"/><rect x="6.5" y="5" width="3" height="9.5" rx="0.5"/><rect x="12" y="1.5" width="3" height="13" rx="0.5"/></svg>
  ),
  gear: (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="8" cy="8" r="2"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2M2.9 2.9l1.4 1.4M11.7 11.7l1.4 1.4M13.1 2.9l-1.4 1.4M4.3 11.7l-1.4 1.4"/></svg>
  ),
};

const NAV_GROUPS = [
  {
    group: 'Monitor',
    items: [
      { to: '/app', label: 'Overview', icon: 'grid', end: true },
      { to: '/app/alerts', label: 'Alerts', icon: 'bell' },
      { to: '/app/traffic', label: 'Traffic Monitor', icon: 'chart' },
    ]
  },
  {
    group: 'Intelligence',
    items: [
      { to: '/app/threats', label: 'Threat Intelligence', icon: 'shield' },
      { to: '/app/investigation', label: 'Investigation', icon: 'grid' },
      { to: '/app/ai', label: 'AI Detection', icon: 'shield' },
    ]
  },
  {
    group: 'System',
    items: [
      { to: '/app/network', label: 'Network Telemetry', icon: 'network' },
      { to: '/app/settings', label: 'Settings', icon: 'gear' },
    ]
  }
];

const FLAT_NAV_ITEMS: VerticalNavItem[] = [
  { to: '/app', label: 'Overview', icon: ICONS.grid, end: true },
  { to: '/app/alerts', label: 'Alerts', icon: ICONS.bell },
  { to: '/app/traffic', label: 'Traffic Monitor', icon: ICONS.chart },
  { to: '/app/threats', label: 'Threat Intelligence', icon: ICONS.shield },
  { to: '/app/investigation', label: 'Investigation', icon: ICONS.grid },
  { to: '/app/ai', label: 'AI Detection', icon: ICONS.shield },
  { to: '/app/network', label: 'Network Telemetry', icon: ICONS.network },
  { to: '/app/settings', label: 'Settings', icon: ICONS.gear },
];

export function AppLayout() {
  const { user, organization, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const { connectionState } = useLiveAlerts();
  const location = useLocation();

  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('irochi-sidebar-collapsed') === 'true';
  });
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const toggleSidebar = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem('irochi-sidebar-collapsed', String(next));
  };

  const handleSignOut = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    logout();
  }, [logout]);

  // Close mobile drawer on escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileDrawerOpen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close mobile drawer on navigation change
  useEffect(() => {
    setMobileDrawerOpen(false);
  }, [location.pathname]);

  const activePageLabel = (() => {
    for (const group of NAV_GROUPS) {
      const match = group.items.find(item => location.pathname.startsWith(item.to) && item.to !== '/app');
      if (match) return match.label;
    }
    return location.pathname === '/app' ? 'Overview' : '';
  })();

  return (
    <div className={`app-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Mobile Drawer Overlay */}
      {mobileDrawerOpen && (
        <div 
          className="mobile-drawer-overlay" 
          onClick={() => setMobileDrawerOpen(false)}
        />
      )}

      {/* Sidebar Rail */}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileDrawerOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-signal-line" />

        <div className="sidebar-brand">
          <Link to="/" className="sidebar-brand-link">
            <IrochiLogo size={24} />
            {!collapsed && (
              <div className="sidebar-brand-meta">
                <span className="sidebar-brand-text">IROCHI</span>
                <span className="sidebar-brand-sub">Passive workspace</span>
              </div>
            )}
          </Link>
          <button 
            className="sidebar-toggle" 
            onClick={toggleSidebar} 
            aria-label="Toggle sidebar panel"
            aria-expanded={!collapsed}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              {collapsed ? <path d="M6 3l5 5-5 5" /> : <path d="M10 3L5 8l5 5" />}
            </svg>
          </button>
        </div>

        {/* Collapsed Mode: Vertical Meniscus Liquid Navigation Rail */}
        {collapsed ? (
          <div className="sidebar-collapsed-rail-container">
            <VerticalMeniscusRail items={FLAT_NAV_ITEMS} />
          </div>
        ) : (
          /* Expanded Mode: Full Grouped Nav */
          <nav className="sidebar-nav">
            {NAV_GROUPS.map((group) => (
              <div key={group.group} className="nav-group">
                <span className="nav-group-label">{group.group}</span>
                {group.items.map(({ to, label, icon, end }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={end}
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  >
                    <span className="nav-icon">{ICONS[icon]}</span>
                    <span className="nav-label">{label}</span>
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
        )}

        <div className="sidebar-footer">
          {/* Connection status */}
          <div className="sidebar-footer-connection" title={`WS telemetry: ${connectionState}`}>
            <span className={`connection-dot ${connectionState}`} />
            {!collapsed && <span className="connection-text">{connectionState === 'live' ? 'Telemetry Live' : connectionState}</span>}
          </div>

          {/* Theme switcher / details */}
          <div className="sidebar-footer-user-row">
            <div className="sidebar-user-avatar" title={`${user?.name} (${user?.role})`}>
              {user?.avatar_initials}
            </div>
            {!collapsed && (
              <div className="sidebar-user-meta">
                <span className="sidebar-user-name">{user?.name}</span>
                <span className="sidebar-user-role">{organization?.name}</span>
              </div>
            )}
            
            <button 
              className="theme-switcher-btn"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              aria-label="Switch visual theme"
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
            >
              {theme === 'dark' ? (
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="8" cy="8" r="3"/><path d="M8 1v1.5M8 13.5v1.5M1 8h1.5M13.5 8H15M3.05 3.05l1.06 1.06M11.89 11.89l1.06 1.06M12.95 3.05l-1.06 1.06M4.11 11.89l-1.06 1.06"/></svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3.5 10.5a5 5 0 1 0 7-7 3.5 3.5 0 0 1-7 7z"/></svg>
              )}
            </button>
          </div>

          {!collapsed && (
            <button className="btn btn-ghost btn-sm btn-logout" onClick={handleSignOut}>
              Sign out
            </button>
          )}
        </div>
      </aside>

      {/* Main Area */}
      <div className="main-area">
        {/* Top Header */}
        <header className="top-header">
          <div className="top-header-left">
            <button 
              className="mobile-menu-trigger" 
              onClick={() => setMobileDrawerOpen(true)}
              aria-label="Open mobile menu"
            >
              <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 5h16M2 10h16M2 15h16" />
              </svg>
            </button>
            <span className="breadcrumb">{activePageLabel}</span>
            <div className="global-search">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="7" cy="7" r="5" />
                <line x1="11" y1="11" x2="15" y2="15" />
              </svg>
              <input type="text" placeholder="Search alerts, IP addresses, connection IDs..." />
            </div>
          </div>
          <div className="top-header-right">
            <div className="header-theme-switcher">
              <button 
                className="theme-switcher-btn"
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? 'Light mode' : 'Dark mode'}
              </button>
            </div>
            <div className="header-divider" />
            <div className="user-menu">
              <div className="user-avatar">{user?.avatar_initials}</div>
              <div className="user-info">
                <span className="user-name">{user?.name}</span>
                <span className="user-role">{user?.role}</span>
              </div>
            </div>
            <button className="btn btn-ghost btn-sm header-logout-btn" onClick={handleSignOut}>
              Sign out
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
