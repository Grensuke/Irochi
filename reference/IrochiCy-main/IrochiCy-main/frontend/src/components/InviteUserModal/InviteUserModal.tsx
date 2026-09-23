import { useState } from 'react';
import Modal from '@/components/Modal/Modal';
import { addToast } from '@/components/Toast/Toast';
import './InviteUserModal.css';

interface InviteUserModalProps { onClose: () => void; }

export default function InviteUserModal({ onClose }: InviteUserModalProps) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'ANALYST' | 'ADMIN'>('ANALYST');

  const handleSend = () => {
    if (!email.includes('@')) { addToast({ type: 'error', title: 'Invalid email address' }); return; }
    addToast({ type: 'success', title: 'Invitation sent', message: `Sent to ${email}` });
    onClose();
  };

  return (
    <Modal title="Invite User" onClose={onClose}>
      <div className="invite-modal">
        <div className="invite-modal__field">
          <label className="invite-modal__label">EMAIL ADDRESS</label>
          <input className="invite-modal__input" type="email" placeholder="analyst@org.com" value={email} onChange={e => setEmail(e.target.value)} />
        </div>
        <div className="invite-modal__field">
          <label className="invite-modal__label">ROLE</label>
          <select className="invite-modal__select" value={role} onChange={e => setRole(e.target.value as 'ANALYST' | 'ADMIN')}>
            <option value="ANALYST">Analyst</option>
            <option value="ADMIN">Admin</option>
          </select>
        </div>
        <button className="invite-modal__btn" onClick={handleSend}>SEND INVITATION</button>
      </div>
    </Modal>
  );
}
