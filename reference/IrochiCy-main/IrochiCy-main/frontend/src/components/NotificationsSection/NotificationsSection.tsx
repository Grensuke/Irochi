import { useUserPreferences } from '@/context/UserPreferencesContext';
import ToggleSwitch from '@/components/ToggleSwitch/ToggleSwitch';
import './NotificationsSection.css';

export default function NotificationsSection() {
  const { prefs, setNotifyCritical, setNotifyHigh, setNotifyReconnect, setNotifyDailySummary, setDailySummaryEmail } = useUserPreferences();

  return (
    <div className="notif-section">
      <div className="notif-section__title">ALERT NOTIFICATION SETTINGS</div>
      <div className="notif-row">
        <span className="notif-row__label">Critical alerts — browser notification</span>
        <ToggleSwitch checked={prefs.notifyCritical} onChange={setNotifyCritical} label="Critical alerts" />
      </div>
      <div className="notif-row">
        <span className="notif-row__label">High severity alerts — toast in dashboard</span>
        <ToggleSwitch checked={prefs.notifyHigh} onChange={setNotifyHigh} label="High alerts" />
      </div>
      <div className="notif-row">
        <span className="notif-row__label">WebSocket reconnection events — status bar</span>
        <ToggleSwitch checked={prefs.notifyReconnect} onChange={setNotifyReconnect} label="Reconnect events" />
      </div>
      <div className="notif-row">
        <span className="notif-row__label">Daily summary — email</span>
        <div className="notif-row__right">
          {prefs.notifyDailySummary && (
            <input className="notif-row__email" type="email" placeholder="analyst@org.com" value={prefs.dailySummaryEmail} onChange={e => setDailySummaryEmail(e.target.value)} />
          )}
          <ToggleSwitch checked={prefs.notifyDailySummary} onChange={setNotifyDailySummary} label="Daily summary" />
        </div>
      </div>
    </div>
  );
}
