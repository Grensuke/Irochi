import { useState } from 'react';
import type { AdminUser } from '@/types';
import ContextMenu, { type ContextMenuItem } from '@/components/ContextMenu/ContextMenu';
import Modal from '@/components/Modal/Modal';
import InviteUserModal from '@/components/InviteUserModal/InviteUserModal';
import { addToast } from '@/components/Toast/Toast';
import './AdminUsers.css';

const MOCK_USERS: AdminUser[] = [
  { id: '1', username: 'admin', displayName: 'System Admin', initials: 'SA', role: 'ADMIN', status: 'active', lastLogin: new Date(Date.now() - 300000).toISOString(), email: 'admin@sih.io' },
  { id: '2', username: 'schen', displayName: 'Sarah Chen', initials: 'SC', role: 'ANALYST', status: 'active', lastLogin: new Date(Date.now() - 1800000).toISOString(), email: 'schen@sih.io' },
  { id: '3', username: 'amorgan', displayName: 'Alex Morgan', initials: 'AM', role: 'ANALYST', status: 'active', lastLogin: new Date(Date.now() - 7200000).toISOString(), email: 'amorgan@sih.io' },
  { id: '4', username: 'jwilson', displayName: 'James Wilson', initials: 'JW', role: 'ANALYST', status: 'suspended', lastLogin: new Date(Date.now() - 86400000).toISOString(), email: 'jwilson@sih.io' },
  { id: '5', username: 'mgarcia', displayName: 'Maria Garcia', initials: 'MG', role: 'ANALYST', status: 'active', lastLogin: new Date(Date.now() - 3600000).toISOString(), email: 'mgarcia@sih.io' },
];

function relativeTime(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function AdminUsers() {
  const [users, setUsers] = useState(MOCK_USERS);
  const [ctx, setCtx] = useState<{ x: number; y: number; userId: string } | null>(null);
  const [confirmModal, setConfirmModal] = useState<{ action: string; userId: string } | null>(null);
  const [inviteOpen, setInviteOpen] = useState(false);

  const getMenuItems = (user: AdminUser): ContextMenuItem[] => [
    { label: 'Edit User', onClick: () => addToast({ type: 'info', title: 'Edit user dialog would open' }) },
    { label: 'Change Role', onClick: () => { setUsers(prev => prev.map(u => u.id === user.id ? { ...u, role: u.role === 'ADMIN' ? 'ANALYST' : 'ADMIN' } : u)); addToast({ type: 'success', title: `Role changed for ${user.displayName}` }); } },
    { label: '', onClick: () => {}, divider: true },
    { label: user.status === 'active' ? 'Suspend Account' : 'Reactivate', onClick: () => setConfirmModal({ action: user.status === 'active' ? 'suspend' : 'reactivate', userId: user.id }), danger: user.status === 'active' },
    { label: 'Reset Password', onClick: () => addToast({ type: 'success', title: `Password reset email sent to ${user.email}` }) },
    { label: 'Delete User', onClick: () => setConfirmModal({ action: 'delete', userId: user.id }), danger: true },
  ];

  const handleConfirm = () => {
    if (!confirmModal) return;
    if (confirmModal.action === 'delete') {
      setUsers(prev => prev.filter(u => u.id !== confirmModal.userId));
      addToast({ type: 'warning', title: 'User deleted' });
    } else if (confirmModal.action === 'suspend') {
      setUsers(prev => prev.map(u => u.id === confirmModal.userId ? { ...u, status: 'suspended' as const } : u));
      addToast({ type: 'warning', title: 'Account suspended' });
    } else {
      setUsers(prev => prev.map(u => u.id === confirmModal.userId ? { ...u, status: 'active' as const } : u));
      addToast({ type: 'success', title: 'Account reactivated' });
    }
    setConfirmModal(null);
  };

  return (
    <div>
      <div className="admin-users__header">
        <span className="admin-users__title">User Management</span>
        <button className="admin-users__invite-btn" onClick={() => setInviteOpen(true)}>INVITE USER</button>
      </div>

      <table className="admin-users__table">
        <thead>
          <tr><th></th><th>USERNAME</th><th>FULL NAME</th><th>ROLE</th><th>LAST LOGIN</th><th>STATUS</th><th></th></tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u.id}>
              <td><span className="admin-users__avatar">{u.initials}</span></td>
              <td><span className="admin-users__username">{u.username}</span></td>
              <td><span className="admin-users__name">{u.displayName}</span></td>
              <td><span className={`admin-users__role-badge admin-users__role--${u.role.toLowerCase()}`}>{u.role}</span></td>
              <td><span className="admin-users__time">{relativeTime(u.lastLogin)}</span></td>
              <td><span className={`admin-users__status admin-users__status--${u.status}`}>{u.status.toUpperCase()}</span></td>
              <td><button className="admin-users__actions-btn" onClick={e => setCtx({ x: e.clientX, y: e.clientY, userId: u.id })}>ACTIONS ▾</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      {ctx && <ContextMenu items={getMenuItems(users.find(u => u.id === ctx.userId)!)} x={ctx.x} y={ctx.y} onClose={() => setCtx(null)} />}

      {confirmModal && (
        <Modal title={`Confirm ${confirmModal.action}`} onClose={() => setConfirmModal(null)}>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-5)' }}>
            Are you sure you want to {confirmModal.action} this user? This action cannot be easily undone.
          </p>
          <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end' }}>
            <button className="admin-users__actions-btn" onClick={() => setConfirmModal(null)}>CANCEL</button>
            <button className="admin-users__invite-btn" style={{ background: 'var(--severity-critical)' }} onClick={handleConfirm}>CONFIRM</button>
          </div>
        </Modal>
      )}

      {inviteOpen && <InviteUserModal onClose={() => setInviteOpen(false)} />}
    </div>
  );
}
