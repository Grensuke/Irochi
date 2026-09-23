import { useLocation } from 'react-router-dom';
import ThemeToggle from '@/components/ThemeToggle/ThemeToggle';
import LiveStatusPill from '@/components/LiveStatusPill/LiveStatusPill';
import type { WebSocketStatus } from '@/types';
import './Header.css';

const ROUTE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/alerts': 'Alerts',
  '/network': 'Network',
  '/threats': 'Threats',
  '/settings': 'Settings',
};

interface HeaderProps {
  sidebarCollapsed: boolean;
  wsStatus: WebSocketStatus;
}

export default function Header({ sidebarCollapsed, wsStatus }: HeaderProps) {
  const location = useLocation();

  // Resolve page title from route
  const pathBase = '/' + location.pathname.split('/').filter(Boolean)[0];
  const title = ROUTE_TITLES[pathBase] || 'SIH·26145';

  return (
    <header className={`app-header ${sidebarCollapsed ? 'app-header--collapsed' : 'app-header--expanded'}`}>
      <h1 className="app-header__title">{title}</h1>
      <div className="app-header__right">
        <LiveStatusPill status={wsStatus} />
        <ThemeToggle />
      </div>
    </header>
  );
}
