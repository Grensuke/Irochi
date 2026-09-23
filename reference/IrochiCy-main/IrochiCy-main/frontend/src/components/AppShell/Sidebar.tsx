import { NavLink } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import './Sidebar.css';

// ─── SVG Icons (18×18) ───
function DashboardIcon() {
  return (
    <svg className="sidebar__nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1.5" y="1.5" width="6" height="6" rx="1" />
      <rect x="10.5" y="1.5" width="6" height="3.5" rx="1" />
      <rect x="10.5" y="8" width="6" height="8.5" rx="1" />
      <rect x="1.5" y="10.5" width="6" height="6" rx="1" />
    </svg>
  );
}

function AlertsIcon() {
  return (
    <svg className="sidebar__nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7.86 2.16a1.25 1.25 0 0 1 2.28 0l5.42 10.84A1.25 1.25 0 0 1 14.44 15H3.56a1.25 1.25 0 0 1-1.12-1.99L7.86 2.16Z" />
      <line x1="9" y1="6.5" x2="9" y2="9.5" />
      <circle cx="9" cy="12" r="0.5" fill="currentColor" />
    </svg>
  );
}

function NetworkIcon() {
  return (
    <svg className="sidebar__nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="3.5" r="2" />
      <circle cx="3.5" cy="14" r="2" />
      <circle cx="14.5" cy="14" r="2" />
      <line x1="9" y1="5.5" x2="5" y2="12" />
      <line x1="9" y1="5.5" x2="13" y2="12" />
      <line x1="5.5" y1="14" x2="12.5" y2="14" />
    </svg>
  );
}

function ThreatsIcon() {
  return (
    <svg className="sidebar__nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 1.5L2 5.5v4c0 4.17 3 7.5 7 8.5 4-1 7-4.33 7-8.5v-4L9 1.5z" />
      <line x1="9" y1="6" x2="9" y2="9.5" />
      <circle cx="9" cy="12" r="0.5" fill="currentColor" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg className="sidebar__nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="9" r="2.5" />
      <path d="M14.7 11.1a1.2 1.2 0 0 0 .24 1.32l.04.04a1.45 1.45 0 1 1-2.05 2.05l-.04-.04a1.2 1.2 0 0 0-1.32-.24 1.2 1.2 0 0 0-.73 1.1v.12a1.45 1.45 0 1 1-2.9 0v-.06a1.2 1.2 0 0 0-.79-1.1 1.2 1.2 0 0 0-1.32.24l-.04.04a1.45 1.45 0 1 1-2.05-2.05l.04-.04a1.2 1.2 0 0 0 .24-1.32 1.2 1.2 0 0 0-1.1-.73h-.12a1.45 1.45 0 1 1 0-2.9h.06a1.2 1.2 0 0 0 1.1-.79 1.2 1.2 0 0 0-.24-1.32l-.04-.04A1.45 1.45 0 1 1 5.42 3.3l.04.04a1.2 1.2 0 0 0 1.32.24h.06a1.2 1.2 0 0 0 .73-1.1v-.12a1.45 1.45 0 0 1 2.9 0v.06a1.2 1.2 0 0 0 .73 1.1 1.2 1.2 0 0 0 1.32-.24l.04-.04a1.45 1.45 0 1 1 2.05 2.05l-.04.04a1.2 1.2 0 0 0-.24 1.32v.06a1.2 1.2 0 0 0 1.1.73h.12a1.45 1.45 0 0 1 0 2.9h-.06a1.2 1.2 0 0 0-1.1.73Z" />
    </svg>
  );
}

function CollapseArrow() {
  return (
    <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="8,2 4,6 8,10" />
    </svg>
  );
}

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
  { to: '/alerts', label: 'Alerts', icon: AlertsIcon },
  { to: '/network', label: 'Network', icon: NetworkIcon },
  { to: '/threats', label: 'Threats', icon: ThreatsIcon },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { user, logout } = useAuth();

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      {/* Brand */}
      <div className="sidebar__brand">
        <span className="sidebar__wordmark">
          {collapsed ? 'S' : 'SIH·26145'}
        </span>
      </div>
      <div className="sidebar__divider" />

      {/* Navigation */}
      <nav className="sidebar__nav">
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            data-tooltip={item.label}
            className={({ isActive }) =>
              `sidebar__nav-item ${isActive ? 'sidebar__nav-item--active' : ''}`
            }
          >
            <item.icon />
            <span className="sidebar__nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User Panel */}
      {user && (
        <div className="sidebar__user">
          <div className="sidebar__avatar">{user.initials}</div>
          <div className="sidebar__user-info">
            <div className="sidebar__username">{user.displayName}</div>
            <div className="sidebar__role">{user.role}</div>
          </div>
        </div>
      )}

      {/* Logout */}
      <button
        className="sidebar__nav-item"
        onClick={logout}
        style={{ border: 'none', background: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', padding: '10px 20px', color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: '11px', letterSpacing: '0.05em' }}
        aria-label="Log out"
      >
        <span className="sidebar__nav-label">{collapsed ? '⏻' : 'LOG OUT'}</span>
      </button>

      {/* Collapse Toggle */}
      <button className="sidebar__toggle" onClick={onToggle} aria-label="Toggle sidebar">
        <CollapseArrow />
      </button>
    </aside>
  );
}
