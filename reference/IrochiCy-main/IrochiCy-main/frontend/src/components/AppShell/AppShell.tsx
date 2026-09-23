import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { useWebSocket } from '@/hooks/useWebSocket';
import useKeyboardShortcuts from '@/hooks/useKeyboardShortcuts';
import ToastContainer from '@/components/Toast/Toast';
import ConnectionLostBanner from '@/components/ConnectionLostBanner/ConnectionLostBanner';
import KeyboardShortcutsModal from '@/components/KeyboardShortcuts/KeyboardShortcutsModal';
import './AppShell.css';

export default function AppShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { status: wsStatus, alerts, latestAlert } = useWebSocket();

  useKeyboardShortcuts();

  // Auto-collapse sidebar on narrow viewports
  useEffect(() => {
    const check = () => { if (window.innerWidth < 1280) setSidebarCollapsed(true); };
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  return (
    <div className="app-shell">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(prev => !prev)}
      />
      <Header
        sidebarCollapsed={sidebarCollapsed}
        wsStatus={wsStatus}
      />
      <ConnectionLostBanner wsStatus={wsStatus} />
      <main className={`app-shell__main ${sidebarCollapsed ? 'app-shell__main--collapsed' : 'app-shell__main--expanded'}`}>
        <div className="app-shell__content">
          <Outlet context={{ wsStatus, alerts, latestAlert }} />
        </div>
      </main>
      <ToastContainer />
      <KeyboardShortcutsModal />
    </div>
  );
}
