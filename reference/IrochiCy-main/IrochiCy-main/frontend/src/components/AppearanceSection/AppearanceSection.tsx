import { useTheme } from '@/hooks/useTheme';
import { useUserPreferences } from '@/context/UserPreferencesContext';
import type { TableDensity, TimestampFormat, FontScale } from '@/types';
import './AppearanceSection.css';

export default function AppearanceSection() {
  const { theme, setTheme } = useTheme();
  const { prefs, setTableDensity, setTimestampFormat, setFontScale } = useUserPreferences();

  return (
    <div className="appearance-section">
      <div className="appearance-section__title">Display Preferences</div>

      {/* Theme */}
      <div className="appearance-section__group">
        <div className="appearance-section__label">THEME</div>
        <div className="appearance-section__cards">
          <div className={`appearance-card ${theme === 'dark' ? 'appearance-card--active' : ''}`} onClick={() => setTheme('dark')}>
            <div className="appearance-card__swatch" style={{ background: '#0F1117' }} />
            <span className="appearance-card__label">DARK</span>
          </div>
          <div className={`appearance-card ${theme === 'light' ? 'appearance-card--active' : ''}`} onClick={() => setTheme('light')}>
            <div className="appearance-card__swatch" style={{ background: '#F4F5F7' }} />
            <span className="appearance-card__label">LIGHT</span>
          </div>
        </div>
      </div>

      {/* Table density */}
      <div className="appearance-section__group">
        <div className="appearance-section__label">TABLE DENSITY</div>
        <div className="appearance-section__cards">
          {(['compact', 'comfortable', 'spacious'] as TableDensity[]).map(d => (
            <div key={d} className={`appearance-card density-card ${prefs.tableDensity === d ? 'appearance-card--active' : ''}`} onClick={() => setTableDensity(d)}>
              <div className="density-card__lines">
                {Array.from({ length: d === 'compact' ? 6 : d === 'comfortable' ? 4 : 3 }, (_, i) => (
                  <div key={i} className="density-card__line" style={{ height: d === 'compact' ? 2 : d === 'comfortable' ? 4 : 6 }} />
                ))}
              </div>
              <span className="appearance-card__label">{d.toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Timestamp format */}
      <div className="appearance-section__group">
        <div className="appearance-section__label">TIMESTAMP FORMAT</div>
        <div className="appearance-section__cards">
          {(['relative', 'absolute'] as TimestampFormat[]).map(f => (
            <div key={f} className={`appearance-card ${prefs.timestampFormat === f ? 'appearance-card--active' : ''}`} onClick={() => setTimestampFormat(f)}>
              <span className="appearance-card__label" style={{ fontSize: 14 }}>{f === 'relative' ? '3m ago' : '14:32:17 UTC'}</span>
              <span className="appearance-card__label">{f.toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Font scale */}
      <div className="appearance-section__group">
        <div className="appearance-section__label">FONT SIZE</div>
        <div className="appearance-section__cards">
          {(['small', 'default', 'large'] as FontScale[]).map(s => (
            <div key={s} className={`appearance-card font-card ${prefs.fontScale === s ? 'appearance-card--active' : ''}`} onClick={() => setFontScale(s)}>
              <span className="font-card__sample" style={{ fontSize: s === 'small' ? 12 : s === 'default' ? 14 : 16 }}>Aa</span>
              <span className="appearance-card__label">{s.toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
