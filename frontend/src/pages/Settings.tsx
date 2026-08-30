/**
 * Settings page — visual/mock screens only.
 *
 * No real CRUD, persistence, authentication, authorization,
 * organization switching, tenant isolation, or permission enforcement.
 * This establishes the product structure for future implementation.
 */

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { MOCK_TEAM_MEMBERS, MOCK_ROLES } from '../services/mockData';
import './Settings.css';

type Tab = 'profile' | 'organization' | 'users' | 'roles' | 'appearance';

export function Settings() {
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const { user, organization } = useAuth();
  const { theme, setTheme } = useTheme();

  const tabs: { key: Tab; label: string }[] = [
    { key: 'profile', label: 'Profile' },
    { key: 'organization', label: 'Organization' },
    { key: 'users', label: 'Users' },
    { key: 'roles', label: 'Roles & Permissions' },
    { key: 'appearance', label: 'Appearance' },
  ];

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1>Settings</h1>
        <span className="demo-badge">MOCK — NO REAL PERSISTENCE</span>
      </div>

      <div className="settings-content">
        <div className="tabs" style={{ padding: '0 var(--space-6)' }}>
          {tabs.map(t => (
            <button
              key={t.key}
              className={`tab ${activeTab === t.key ? 'active' : ''}`}
              onClick={() => setActiveTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="settings-body">
          {activeTab === 'profile' && (
            <div className="settings-section animate-fade-in">
              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Profile</span>
                </div>
                <div className="panel-body settings-form">
                  <div className="profile-avatar-section">
                    <div className="profile-avatar-lg">{user?.avatar_initials}</div>
                    <div className="profile-avatar-info">
                      <span className="profile-name">{user?.name}</span>
                      <span className="profile-role">{user?.role}</span>
                    </div>
                  </div>
                  <div className="form-grid">
                    <div className="input-group">
                      <label className="input-label">Full Name</label>
                      <input className="input" defaultValue={user?.name} disabled />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Email</label>
                      <input className="input" defaultValue={user?.email} disabled />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Role</label>
                      <input className="input" defaultValue={user?.role} disabled />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'organization' && (
            <div className="settings-section animate-fade-in">
              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Organization</span>
                </div>
                <div className="settings-planned-banner">
                  <span className="planned-dot" />
                  <span>Planned: Backend persistence for organization configuration is in development.</span>
                </div>
                <div className="panel-body settings-form">
                  <div className="form-grid">
                    <div className="input-group">
                      <label className="input-label">Organization Name</label>
                      <input className="input" defaultValue={organization?.name} disabled />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Plan</label>
                      <input className="input" defaultValue={organization?.plan} disabled />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Organization ID</label>
                      <input className="input mono" defaultValue={organization?.id} disabled />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'users' && (
            <div className="settings-section animate-fade-in">
              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Team Members</span>
                  <button className="btn btn-ghost btn-sm" disabled>Invite User</button>
                </div>
                <div className="settings-planned-banner">
                  <span className="planned-dot" />
                  <span>Planned: User invitations and status tracking require active PostgreSQL database persistence.</span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {MOCK_TEAM_MEMBERS.map(m => (
                        <tr key={m.id}>
                          <td>{m.name}</td>
                          <td className="mono">{m.email}</td>
                          <td>{m.role}</td>
                          <td>
                            <span className={`user-status-badge ${m.status}`}>{m.status}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'roles' && (
            <div className="settings-section animate-fade-in">
              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Roles &amp; Permissions</span>
                  <button className="btn btn-ghost btn-sm" disabled>Create Role</button>
                </div>
                <div className="settings-planned-banner">
                  <span className="planned-dot" />
                  <span>Planned: Role-Based Access Control (RBAC) is mock only; authorization policies are in development.</span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Role</th>
                        <th>Description</th>
                        <th>Users</th>
                      </tr>
                    </thead>
                    <tbody>
                      {MOCK_ROLES.map(r => (
                        <tr key={r.name}>
                          <td style={{ fontWeight: 600 }}>{r.name}</td>
                          <td style={{ color: 'var(--text-secondary)' }}>{r.description}</td>
                          <td className="mono">{r.users}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="settings-section animate-fade-in">
              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Appearance Settings</span>
                </div>
                <div className="panel-body settings-form">
                  <div className="input-group">
                    <label className="input-label">Theme Mode</label>
                    <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
                      <button
                        className={`btn ${theme === 'dark' ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setTheme('dark')}
                      >
                        Dark Theme (SOC Ops)
                      </button>
                      <button
                        className={`btn ${theme === 'light' ? 'btn-primary' : 'btn-ghost'}`}
                        onClick={() => setTheme('light')}
                      >
                        Light Theme (Enterprise)
                      </button>
                    </div>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 'var(--space-2)' }}>
                      Theme preferences are persisted to your browser storage and synchronize across the public workspace.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
