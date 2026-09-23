import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { UserPreferences, TableDensity, TimestampFormat, FontScale, ThemeMode } from '@/types';
import { useTheme } from '@/hooks/useTheme';

const STORAGE_KEY = 'sih-prefs';

const DEFAULT_PREFS: UserPreferences = {
  theme: 'dark',
  tableDensity: 'comfortable',
  timestampFormat: 'relative',
  fontScale: 'default',
  notifyCritical: true,
  notifyHigh: true,
  notifyReconnect: true,
  notifyDailySummary: false,
  dailySummaryEmail: '',
};

interface UserPreferencesContextValue {
  prefs: UserPreferences;
  setTableDensity: (v: TableDensity) => void;
  setTimestampFormat: (v: TimestampFormat) => void;
  setFontScale: (v: FontScale) => void;
  setNotifyCritical: (v: boolean) => void;
  setNotifyHigh: (v: boolean) => void;
  setNotifyReconnect: (v: boolean) => void;
  setNotifyDailySummary: (v: boolean) => void;
  setDailySummaryEmail: (v: string) => void;
}

const UserPreferencesCtx = createContext<UserPreferencesContextValue | null>(null);

export function UserPreferencesProvider({ children }: { children: ReactNode }) {
  const { theme } = useTheme();
  const [prefs, setPrefs] = useState<UserPreferences>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? { ...DEFAULT_PREFS, ...JSON.parse(stored) } : { ...DEFAULT_PREFS, theme };
    } catch {
      return { ...DEFAULT_PREFS, theme };
    }
  });

  // Sync theme from ThemeContext
  useEffect(() => {
    setPrefs(p => ({ ...p, theme: theme as ThemeMode }));
  }, [theme]);

  // Apply font scale
  useEffect(() => {
    const root = document.documentElement;
    const scales: Record<FontScale, string> = { small: '-1', default: '0', large: '1' };
    root.style.setProperty('--font-scale-offset', scales[prefs.fontScale]);
    // Persist
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  }, [prefs]);

  const update = <K extends keyof UserPreferences>(key: K, val: UserPreferences[K]) =>
    setPrefs(p => ({ ...p, [key]: val }));

  return (
    <UserPreferencesCtx.Provider value={{
      prefs,
      setTableDensity: v => update('tableDensity', v),
      setTimestampFormat: v => update('timestampFormat', v),
      setFontScale: v => update('fontScale', v),
      setNotifyCritical: v => update('notifyCritical', v),
      setNotifyHigh: v => update('notifyHigh', v),
      setNotifyReconnect: v => update('notifyReconnect', v),
      setNotifyDailySummary: v => update('notifyDailySummary', v),
      setDailySummaryEmail: v => update('dailySummaryEmail', v),
    }}>
      {children}
    </UserPreferencesCtx.Provider>
  );
}

export function useUserPreferences() {
  const ctx = useContext(UserPreferencesCtx);
  if (!ctx) throw new Error('useUserPreferences must be used within UserPreferencesProvider');
  return ctx;
}
