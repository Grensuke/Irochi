/**
 * Authenticated application shell — sidebar navigation + top header.
 */

import { NavLink, Outlet, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useLiveAlerts } from '../hooks/useLiveAlerts';
import './AppLayout.css';

const NAV_ITEMS = [
  { to: '/app', label: 'Overview', icon: 'grid', end: true },
  { to: '/app/alerts', label: 'Alerts', icon: 'bell' },
  { to: '/app/threats', label: 'Threats', icon: 'shield' },
  { to: '/app/network', label: 'Network', icon: 'network' },
  { to: '/app/analytics', label: 'Analytics', icon: 'chart' },
  { to: '/app/settings', label: 'Settings', icon: 'gear' },
];

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

export function AppLayout() {
  const { user, organization, logout } = useAuth();
  const { connectionState } = useLiveAlerts();
  const location = useLocation();

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="8" stroke="var(--accent-primary)" strokeWidth="1.5" fill="none" />
            <circle cx="10" cy="10" r="3" fill="var(--accent-primary)" />
            <line x1="10" y1="2" x2="10" y2="6" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="10" y1="14" x2="10" y2="18" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="2" y1="10" x2="6" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
            <line x1="14" y1="10" x2="18" y2="10" stroke="var(--accent-primary)" strokeWidth="1.5" />
          </svg>
          <span className="sidebar-brand-text">IROCHI</span>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ to, label, icon, end }) => (
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
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-org">
            <span className="sidebar-org-name">{organization?.name}</span>
            <span className="sidebar-org-plan">{organization?.plan}</span>
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <div className="main-area">
        {/* Top Header */}
        <header className="top-header">
          <div className="top-header-left">
            <span className="breadcrumb">
              {NAV_ITEMS.find(n => location.pathname.startsWith(n.to) && n.to !== '/app')?.label
                ?? (location.pathname === '/app' ? 'Overview' : '')}
            </span>
          </div>
          <div className="top-header-right">
            <div className="connection-indicator">
              <span className={`connection-dot ${connectionState}`} />
              <span className="connection-label">
                {connectionState === 'live' ? 'Live' : connectionState}
              </span>
            </div>
            <div className="header-divider" />
            <div className="user-menu">
              <div className="user-avatar">{user?.avatar_initials}</div>
              <div className="user-info">
                <span className="user-name">{user?.name}</span>
                <span className="user-role">{user?.role}</span>
              </div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={logout}>
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
