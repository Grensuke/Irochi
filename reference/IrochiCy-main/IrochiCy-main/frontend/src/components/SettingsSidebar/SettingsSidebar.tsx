import { useAuth } from '@/context/AuthContext';
import './SettingsSidebar.css';

interface SettingsSidebarProps { active: string; onNavigate: (section: string) => void; }

const NAV_ITEMS = [
  { id: 'profile', label: 'Profile' },
  { id: 'appearance', label: 'Appearance' },
  { id: 'notifications', label: 'Notifications' },
];

const ADMIN_ITEMS = [
  { id: 'api', label: 'API Access' },
  { id: 'users', label: 'Users' },
  { id: 'system', label: 'System' },
];

export default function SettingsSidebar({ active, onNavigate }: SettingsSidebarProps) {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  return (
    <nav className="settings-sidebar">
      {NAV_ITEMS.map(item => (
        <div
          key={item.id}
          className={`settings-sidebar__item ${active === item.id ? 'settings-sidebar__item--active' : ''}`}
          onClick={() => onNavigate(item.id)}
        >{item.label}</div>
      ))}
      {isAdmin && (
        <>
          <div className="settings-sidebar__divider" />
          <div className="settings-sidebar__label">ADMIN</div>
          {ADMIN_ITEMS.map(item => (
            <div
              key={item.id}
              className={`settings-sidebar__item ${active === item.id ? 'settings-sidebar__item--active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >{item.label}</div>
          ))}
        </>
      )}
    </nav>
  );
}
