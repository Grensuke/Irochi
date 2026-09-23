import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import SettingsSidebar from '@/components/SettingsSidebar/SettingsSidebar';
import ProfileSection from '@/components/ProfileSection/ProfileSection';
import AppearanceSection from '@/components/AppearanceSection/AppearanceSection';
import NotificationsSection from '@/components/NotificationsSection/NotificationsSection';
import AdminUsers from '@/components/AdminUsers/AdminUsers';
import AdminSystem from '@/components/AdminSystem/AdminSystem';
import Modal from '@/components/Modal/Modal';
import PageTransition from '@/components/PageTransition/PageTransition';
import { addToast } from '@/components/Toast/Toast';
import './SettingsPage.css';

function ApiAccessSection() {
  const [revealed, setRevealed] = useState(false);
  const [confirmRegen, setConfirmRegen] = useState(false);
  const token = 'sih_tok_a3f8c2d1e5b74909abcdef1234567890abcdef1234567890';

  const handleCopy = () => {
    navigator.clipboard.writeText(token);
    addToast({ type: 'success', title: 'Token copied to clipboard' });
  };

  const handleRegen = () => {
    setConfirmRegen(false);
    addToast({ type: 'warning', title: 'API token regenerated', message: 'Previous token is now invalid' });
  };

  return (
    <div className="api-access">
      <div className="api-access__title">API TOKEN</div>
      <div className="api-access__token-box">
        <span className="api-access__token">{revealed ? token : '•'.repeat(48)}</span>
      </div>
      <div className="api-access__btns">
        <button className="api-access__btn" onClick={() => setRevealed(r => !r)}>{revealed ? 'HIDE' : 'REVEAL'}</button>
        <button className="api-access__btn" onClick={handleCopy}>COPY</button>
        <button className="api-access__btn api-access__btn--danger" onClick={() => setConfirmRegen(true)}>REGENERATE</button>
      </div>
      {confirmRegen && (
        <Modal title="Regenerate API Token" onClose={() => setConfirmRegen(false)}>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-5)' }}>
            This will invalidate your current token. All scripts and integrations using it will stop working. Continue?
          </p>
          <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end' }}>
            <button className="api-access__btn" onClick={() => setConfirmRegen(false)}>CANCEL</button>
            <button className="api-access__btn api-access__btn--danger" onClick={handleRegen}>REGENERATE</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const [section, setSection] = useState('profile');
  const isAdmin = user?.role === 'ADMIN';

  const renderContent = () => {
    switch (section) {
      case 'profile': return <ProfileSection />;
      case 'appearance': return <AppearanceSection />;
      case 'notifications': return <NotificationsSection />;
      case 'api': return isAdmin ? <ApiAccessSection /> : null;
      case 'users': return isAdmin ? <AdminUsers /> : null;
      case 'system': return isAdmin ? <AdminSystem /> : null;
      default: return <ProfileSection />;
    }
  };

  return (
    <PageTransition>
      <div className="settings-page">
        <SettingsSidebar active={section} onNavigate={setSection} />
        <div className="settings-page__content">{renderContent()}</div>
      </div>
    </PageTransition>
  );
}
