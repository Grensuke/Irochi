import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { addToast } from '@/components/Toast/Toast';
import './ProfileSection.css';

const AVATAR_COLORS = ['#FF3B5C', '#FF7A2F', '#A78BFA', '#5B8CFF', '#F5C518', '#00C2A8', '#E879F9'];

export default function ProfileSection() {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.displayName || '');
  const [avatarColor, setAvatarColor] = useState(AVATAR_COLORS[0]);
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');

  const handleUpdatePwd = () => {
    if (!currentPwd || !newPwd) return;
    if (newPwd !== confirmPwd) { addToast({ type: 'error', title: 'Passwords do not match' }); return; }
    addToast({ type: 'success', title: 'Password updated' });
    setCurrentPwd(''); setNewPwd(''); setConfirmPwd('');
  };

  return (
    <div className="profile-section">
      {/* Avatar */}
      <div className="profile-section__avatar" style={{ backgroundColor: avatarColor }} onClick={() => setAvatarColor(AVATAR_COLORS[(AVATAR_COLORS.indexOf(avatarColor) + 1) % AVATAR_COLORS.length])}>
        {user?.initials || 'AN'}
      </div>
      <div className="profile-section__username">{user?.username || 'analyst'}</div>
      <span className={`profile-section__role profile-section__role--${(user?.role || 'ANALYST').toLowerCase()}`}>{user?.role || 'ANALYST'}</span>

      <div className="profile-section__divider" />

      {/* Full name */}
      <div className="profile-section__field">
        <label className="profile-section__label">FULL NAME</label>
        <input className="profile-section__input" type="text" value={fullName} onChange={e => setFullName(e.target.value)} />
      </div>

      <div className="profile-section__divider" />

      {/* Change password */}
      <div className="profile-section__subtitle">CHANGE PASSWORD</div>
      <div className="profile-section__field">
        <label className="profile-section__label">CURRENT PASSWORD</label>
        <input className="profile-section__input" type="password" value={currentPwd} onChange={e => setCurrentPwd(e.target.value)} />
      </div>
      <div className="profile-section__field">
        <label className="profile-section__label">NEW PASSWORD</label>
        <input className="profile-section__input" type="password" value={newPwd} onChange={e => setNewPwd(e.target.value)} />
      </div>
      <div className="profile-section__field">
        <label className="profile-section__label">CONFIRM NEW PASSWORD</label>
        <input className="profile-section__input" type="password" value={confirmPwd} onChange={e => setConfirmPwd(e.target.value)} />
      </div>
      <button className="profile-section__btn" onClick={handleUpdatePwd}>UPDATE PASSWORD</button>
    </div>
  );
}
