import { useTranslation } from 'react-i18next';
import './About.css';

export function About() {
  const { t } = useTranslation();

  return (
    <div className="about-page">
      <div className="about-container">
        {/* Header */}
        <section className="about-header scroll-reveal">
          <div className="section-eyebrow">{t('about.eyebrow', 'ABOUT VIBHINETRA')}</div>
          <h1 className="about-title">
            {t('about.title1', 'Passive observation.')}<br />
            {t('about.title2', 'Precise intelligence.')}
          </h1>
          <p className="about-subtitle">
            {t('about.subtitle', 'Vibhinetra is a passive, real-time threat-detection and security-intelligence system designed for unidirectional IP traffic segments.')}
          </p>
        </section>

        {/* SIH Context & Mission */}
        <section className="about-grid scroll-reveal">
          <div className="about-card">
            <h2 className="about-card-title">{t('about.missionTitle', 'Project Mission')}</h2>
            <p className="about-card-text">
              {t('about.missionText', 'Developed under SIH2026 Problem Statement SIH26145, Vibhinetra addresses the need for robust threat visibility in critical, highly sensitive, or one-directional network taps. It gathers packet telemetry, normalizes features, and processes indicators of compromise without ever writing to or disrupting the live path.')}
            </p>
          </div>

          <div className="about-card">
            <h2 className="about-card-title">{t('about.whyPassiveTitle', 'Why Passive Matters')}</h2>
            <p className="about-card-text">
              {t('about.whyPassiveText', 'In industrial control systems (ICS/SCADA), tactical networks, and high-security air-gapped zones, networks are often coupled via physical data diodes or unidirectional mirrors. Because packet injection can trigger emergency faults, active probes or inline blocking devices are prohibited. Passive detection ensures zero operational interference.')}
            </p>
          </div>
        </section>

        {/* Philosophy & Constraints */}
        <section className="about-philosophy scroll-reveal">
          <h2 className="section-title-sm">{t('about.principlesTitle', 'Operational Principles')}</h2>
          <div className="philosophy-grid">
            <div className="phi-item">
              <div className="phi-icon">✓</div>
              <div>
                <h3 className="phi-title">{t('about.phi1Title', 'Passivity Over Mitigation')}</h3>
                <p className="phi-text">{t('about.phi1Text', 'We observe telemetry passively. Network state changes remain the sole authority of the administrator.')}</p>
              </div>
            </div>
            <div className="phi-item">
              <div className="phi-icon">✓</div>
              <div>
                <h3 className="phi-title">{t('about.phi2Title', 'Evidence Over Intuition')}</h3>
                <p className="phi-text">{t('about.phi2Text', 'Every threat alert is presented alongside exact network logs, confidence values, and timeline summaries.')}</p>
              </div>
            </div>
            <div className="phi-item">
              <div className="phi-icon">✓</div>
              <div>
                <h3 className="phi-title">{t('about.phi3Title', 'Metadata Over Payloads')}</h3>
                <p className="phi-text">{t('about.phi3Text', 'Analyses are performed on headers, connection parameters, and TLS handshakes, respecting privacy and encryption limits.')}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Boundary constraints */}
        <section className="about-boundaries scroll-reveal">
          <div className="boundaries-box">
            <h2 className="boundaries-title">{t('about.invariantsTitle', 'System Invariants')}</h2>
            <p className="boundaries-subtitle">
              {t('about.invariantsSubtitle', "To guarantee architectural compliance, the following actions are strictly outside Vibhinetra's domain:")}
            </p>
            <ul className="boundaries-list">
              <li><strong>{t('about.inv1Title', 'No Packet Injections:')}</strong> {t('about.inv1Text', 'The system does not transmit packets into the monitored network segment.')}</li>
              <li><strong>{t('about.inv2Title', 'No Automatic Blocking:')}</strong> {t('about.inv2Text', 'Actions like firewall modifications, route changes, or socket drops are never executed automatically.')}</li>
              <li><strong>{t('about.inv3Title', 'No Active Taps:')}</strong> {t('about.inv3Text', 'Vibhinetra relies entirely on passive mirrors (SPAN ports) or external export logs (NetFlow/IPFIX).')}</li>
              <li><strong>{t('about.inv4Title', 'No Payloads Decryption:')}</strong> {t('about.inv4Text', 'Network sessions are analyzed using structural header features and TLS handshake indicators.')}</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  );
}
