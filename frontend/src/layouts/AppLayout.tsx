/**
 * Authenticated application shell — sidebar navigation + top header.
 * 
 * Features:
 * - Collapsed sidebar transforms into a vertical Meniscus liquid navigation rail
 * - Monochrome black and grey palette with metallic silver highlights and illuminated active bead
 * - Responsive desktop sidebar & mobile drawer overlay
 */

import { NavLink, Link, Outlet, useLocation } from 'react-router-dom';
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useLiveAlerts } from '../hooks/useLiveAlerts';
import { useNotifications } from '../contexts/NotificationContext';
import { VerticalMeniscusRail } from '../components/VerticalMeniscusRail';
import type { VerticalNavItem } from '../components/VerticalMeniscusRail';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { VibhinetraLogo } from '../components/VibhinetraLogo';
import { NotificationBell } from '../components/NotificationBell';
import { AlertToastStack } from '../components/AlertToast';
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

export function AppLayout() {
  const { user, organization, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const { t } = useTranslation();
  const { liveAlerts, connectionState } = useLiveAlerts();
  const { ingestAlert } = useNotifications();
  const location = useLocation();
  const lastProcessedRef = useRef(0);

  // Feed live alerts into the notification system (critical & high only)
  useEffect(() => {
    if (liveAlerts.length === 0) return;
    // Process only newly added alerts (at the front of the array)
    const newAlerts = liveAlerts.filter(
      (la) => la.receivedAt > lastProcessedRef.current,
    );
    if (newAlerts.length > 0) {
      lastProcessedRef.current = Math.max(...newAlerts.map((a) => a.receivedAt));
      newAlerts.forEach((la) => ingestAlert(la.alert, la.phase));
    }
  }, [liveAlerts, ingestAlert]);

  // ── Demo Alert Simulator ──────────────────────────────────
  // When the WebSocket is disconnected (no backend), simulate
  // critical/high alerts to demonstrate the notification system.
  const demoCounterRef = useRef(0);
  useEffect(() => {
    if (connectionState !== 'disconnected') return;

    const DEMO_ALERTS = [
      {
        threat_type: 'volumetric_ddos' as const,
        severity: 'critical' as const,
        src_ip: '192.168.24.17',
        dst_ip: '10.42.8.21',
        dst_port: 443,
        evidence_summary: 'SYN flood detected — 14,000 packets/sec exceeding baseline by 800%. Active volumetric attack in progress.',
        detector_id: 'ddos_detector' as const,
      },
      {
        threat_type: 'data_exfiltration' as const,
        severity: 'critical' as const,
        src_ip: '10.0.1.200',
        dst_ip: '203.0.113.88',
        dst_port: 443,
        evidence_summary: 'Sustained outbound transfer of 4.2 GB exceeding historical baseline by 400%. Possible data exfiltration.',
        detector_id: 'exfiltration_detector' as const,
      },
      {
        threat_type: 'c2_beaconing' as const,
        severity: 'high' as const,
        src_ip: '10.0.5.20',
        dst_ip: '198.51.100.42',
        dst_port: 443,
        evidence_summary: 'Periodic TLS connections with strict 60s jitter and suspicious SNI pattern detected.',
        detector_id: 'tls_c2_detector' as const,
      },
      {
        threat_type: 'recon_portscan' as const,
        severity: 'high' as const,
        src_ip: '10.0.4.55',
        dst_ip: '10.42.8.0',
        dst_port: 22,
        evidence_summary: 'Sequential horizontal port scan targeting 256 hosts on internal subnet 10.42.8.0/24.',
        detector_id: 'recon_detector' as const,
      },
      {
        threat_type: 'dga_dns_tunnel' as const,
        severity: 'critical' as const,
        src_ip: '10.0.3.42',
        dst_ip: '8.8.8.8',
        dst_port: 53,
        evidence_summary: 'High-entropy DNS queries at 300 req/min — DGA algorithm fingerprint matches known malware family.',
        detector_id: 'dns_dga_tunnel_detector' as const,
      },
    ];

    // Fire first demo alert after 3 seconds, then every 12-20s
    const fireDemo = () => {
      const idx = demoCounterRef.current % DEMO_ALERTS.length;
      const template = DEMO_ALERTS[idx];
      const now = new Date();
      const demoAlert = {
        alert_id: `DEMO-${Date.now()}-${idx}`,
        timestamp: now.toISOString(),
        threat_type: template.threat_type,
        severity: template.severity,
        confidence: 0.92 + Math.random() * 0.06,
        entity_type: 'pair' as const,
        entity_key: `${template.src_ip}-${template.dst_ip}`,
        first_seen_at: new Date(now.getTime() - 60000).toISOString(),
        last_seen_at: now.toISOString(),
        resolved_at: null,
        src_ip: template.src_ip,
        dst_ip: template.dst_ip,
        dst_port: template.dst_port,
        status: 'new' as const,
        evidence_summary: template.evidence_summary,
        detector_id: template.detector_id,
      };
      ingestAlert(demoAlert, 'live');
      demoCounterRef.current++;
    };

    const initialTimer = setTimeout(fireDemo, 3000);
    const interval = setInterval(fireDemo, 12000 + Math.random() * 8000);

    return () => {
      clearTimeout(initialTimer);
      clearInterval(interval);
    };
  }, [connectionState, ingestAlert]);

  const navGroups = useMemo(() => [
    {
      group: t('navGroups.monitor', 'Monitor'),
      items: [
        { to: '/app', label: t('nav.overview', 'Overview'), icon: 'grid', end: true },
        { to: '/app/alerts', label: t('nav.alerts', 'Alerts'), icon: 'bell' },
        { to: '/app/traffic', label: t('nav.trafficMonitor', 'Traffic Monitor'), icon: 'chart' },
      ]
    },
    {
      group: t('navGroups.intelligence', 'Intelligence'),
      items: [
        { to: '/app/investigation', label: t('nav.investigation', 'Investigation'), icon: 'grid' },
      ]
    },
    {
      group: t('navGroups.system', 'System'),
      items: [
        { to: '/app/network', label: t('nav.networkTelemetry', 'Network Telemetry'), icon: 'network' },
        { to: '/app/settings', label: t('nav.settings', 'Settings'), icon: 'gear' },
      ]
    }
  ], [t]);

  const flatNavItems: VerticalNavItem[] = useMemo(() => [
    { to: '/app', label: t('nav.overview', 'Overview'), icon: ICONS.grid, end: true },
    { to: '/app/alerts', label: t('nav.alerts', 'Alerts'), icon: ICONS.bell },
    { to: '/app/traffic', label: t('nav.trafficMonitor', 'Traffic Monitor'), icon: ICONS.chart },
    { to: '/app/investigation', label: t('nav.investigation', 'Investigation'), icon: ICONS.grid },
    { to: '/app/network', label: t('nav.networkTelemetry', 'Network Telemetry'), icon: ICONS.network },
    { to: '/app/settings', label: t('nav.settings', 'Settings'), icon: ICONS.gear },
  ], [t]);

  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('vibhinetra-sidebar-collapsed') === 'true';
  });
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const toggleSidebar = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem('vibhinetra-sidebar-collapsed', String(next));
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
    for (const group of navGroups) {
      const match = group.items.find(item => location.pathname.startsWith(item.to) && item.to !== '/app');
      if (match) return match.label;
    }
    return location.pathname === '/app' ? t('nav.overview', 'Overview') : '';
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
            <VibhinetraLogo size={24} />
            {!collapsed && (
              <div className="sidebar-brand-meta">
                <span className="sidebar-brand-text">VIBHINETRA</span>
                <span className="sidebar-brand-sub">Passive workspace</span>
              </div>
            )}
          </Link>
          <button 
            className="sidebar-toggle" 
            onClick={toggleSidebar} 
            aria-label="Toggle sidebar panel"
            aria-expanded={!collapsed}
            title={collapsed ? t('header.expandSidebar', 'Expand sidebar') : t('header.collapseSidebar', 'Collapse sidebar')}
          >
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              {collapsed ? <path d="M6 3l5 5-5 5" /> : <path d="M10 3L5 8l5 5" />}
            </svg>
          </button>
        </div>

        {/* Collapsed Mode: Vertical Meniscus Liquid Navigation Rail */}
        {collapsed ? (
          <div className="sidebar-collapsed-rail-container">
            <VerticalMeniscusRail items={flatNavItems} />
          </div>
        ) : (
          /* Expanded Mode: Full Grouped Nav */
          <nav className="sidebar-nav">
            {navGroups.map((group) => (
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
            {!collapsed && <span className="connection-text">{connectionState === 'live' ? t('header.telemetryLive', 'Telemetry Live') : t(`connection.${connectionState}`, connectionState)}</span>}
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
              title={theme === 'dark' ? t('common.switchToLight', 'Switch to Light mode') : t('common.switchToDark', 'Switch to Dark mode')}
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
              {t('common.signOut')}
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
              <input type="text" placeholder={t('common.search', 'Search alerts, IP addresses, connection IDs...')} />
            </div>
          </div>
          <div className="top-header-right">
            <div className="header-utility-actions">
              <NotificationBell />
              <div className="header-divider" />
              <LanguageSwitcher compact />
              <button 
                className="theme-switcher-btn header-theme-btn"
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                aria-label="Toggle theme"
                title={theme === 'dark' ? t('common.switchToLight') : t('common.switchToDark')}
              >
                {theme === 'dark' ? (
                  <>
                    <svg className="theme-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="5" />
                      <line x1="12" y1="1" x2="12" y2="3" />
                      <line x1="12" y1="21" x2="12" y2="23" />
                      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                      <line x1="1" y1="12" x2="3" y2="12" />
                      <line x1="21" y1="12" x2="23" y2="12" />
                      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                    </svg>
                    <span className="theme-btn-label">{t('common.lightMode')}</span>
                  </>
                ) : (
                  <>
                    <svg className="theme-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                    </svg>
                    <span className="theme-btn-label">{t('common.darkMode')}</span>
                  </>
                )}
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
              {t('common.signOut')}
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content">
          <Outlet />
        </main>
      </div>

      {/* On-screen alert toasts */}
      <AlertToastStack />
    </div>
  );
}
