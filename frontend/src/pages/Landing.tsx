import { Link } from 'react-router-dom';
import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { UnidirectionalThreatStream } from '../components/UnidirectionalThreatStream';
import './Landing.css';



export function Landing() {
  const [deepDiveOpen, setDeepDiveOpen] = useState(false);
  const { t } = useTranslation();

  const CAPABILITIES = useMemo(() => [
    { title: t('landing.cap1Title'), desc: t('landing.cap1Desc'), signal: t('landing.cap1Signal') },
    { title: t('landing.cap2Title'), desc: t('landing.cap2Desc'), signal: t('landing.cap2Signal') },
    { title: t('landing.cap3Title'), desc: t('landing.cap3Desc'), signal: t('landing.cap3Signal') },
    { title: t('landing.cap4Title'), desc: t('landing.cap4Desc'), signal: t('landing.cap4Signal') },
    { title: t('landing.cap5Title'), desc: t('landing.cap5Desc'), signal: t('landing.cap5Signal') },
    { title: t('landing.cap6Title'), desc: t('landing.cap6Desc'), signal: t('landing.cap6Signal') },
  ], [t]);

  const PIPELINE_STAGES = useMemo(() => [
    { step: '01', name: t('landing.pipe1Name'), desc: t('landing.pipe1Desc') },
    { step: '02', name: t('landing.pipe2Name'), desc: t('landing.pipe2Desc') },
    { step: '03', name: t('landing.pipe3Name'), desc: t('landing.pipe3Desc') },
    { step: '04', name: t('landing.pipe4Name'), desc: t('landing.pipe4Desc') },
    { step: '05', name: t('landing.pipe5Name'), desc: t('landing.pipe5Desc') },
    { step: '06', name: t('landing.pipe6Name'), desc: t('landing.pipe6Desc') },
  ], [t]);

  const THREAT_DEEP_DIVE = useMemo(() => [
    { label: t('landing.threat1Label'), description: t('landing.threat1Desc'), indicators: [t('landing.threat1Ind1'), t('landing.threat1Ind2'), t('landing.threat1Ind3'), t('landing.threat1Ind4')] },
    { label: t('landing.threat2Label'), description: t('landing.threat2Desc'), indicators: [t('landing.threat2Ind1'), t('landing.threat2Ind2'), t('landing.threat2Ind3'), t('landing.threat2Ind4')] },
    { label: t('landing.threat3Label'), description: t('landing.threat3Desc'), indicators: [t('landing.threat3Ind1'), t('landing.threat3Ind2'), t('landing.threat3Ind3'), t('landing.threat3Ind4')] },
    { label: t('landing.threat4Label'), description: t('landing.threat4Desc'), indicators: [t('landing.threat4Ind1'), t('landing.threat4Ind2'), t('landing.threat4Ind3'), t('landing.threat4Ind4')] },
    { label: t('landing.threat5Label'), description: t('landing.threat5Desc'), indicators: [t('landing.threat5Ind1'), t('landing.threat5Ind2'), t('landing.threat5Ind3'), t('landing.threat5Ind4')] },
    { label: t('landing.threat6Label'), description: t('landing.threat6Desc'), indicators: [t('landing.threat6Ind1'), t('landing.threat6Ind2'), t('landing.threat6Ind3'), t('landing.threat6Ind4')] },
    { label: t('landing.threat7Label'), description: t('landing.threat7Desc'), indicators: [t('landing.threat7Ind1'), t('landing.threat7Ind2'), t('landing.threat7Ind3'), t('landing.threat7Ind4')] },
  ], [t]);

  const DETECTOR_DEEP_DIVE = useMemo(() => [
    { label: t('landing.det1Label'), description: t('landing.det1Desc'), threats: [t('landing.threat1Label')], method: t('landing.det1Method') },
    { label: t('landing.det2Label'), description: t('landing.det2Desc'), threats: [t('landing.threat5Label')], method: t('landing.det2Method') },
    { label: t('landing.det3Label'), description: t('landing.det3Desc'), threats: [t('landing.threat3Label')], method: t('landing.det3Method') },
    { label: t('landing.det4Label'), description: t('landing.det4Desc'), threats: [t('landing.threat2Label'), t('landing.threat4Label')], method: t('landing.det4Method') },
    { label: t('landing.det5Label'), description: t('landing.det5Desc'), threats: [t('landing.threat6Label')], method: t('landing.det5Method') },
  ], [t]);

  return (
    <div className="landing-page-wrap">
      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-spotlight-beam" />
        <div className="landing-hero-container">
          <div className="hero-text-content">
            <div className="hero-eyebrow">{t('landing.heroEyebrow')}</div>
            <h1 className="hero-title">
              {t('landing.heroTitle1')}<br />
              {t('landing.heroTitle2')}
            </h1>
            <p className="hero-description">
              {t('landing.heroDescription')}
            </p>
            <div className="hero-actions">
              <Link to="/login" className="btn btn-primary btn-lg">
                {t('common.explorePlatform')}
              </Link>
              <Link to="/architecture" className="btn btn-ghost btn-lg">
                {t('common.viewArchitecture')}
              </Link>
            </div>

            {/* Passive Warning Banner */}
            <div className="passive-warning-banner">
              <span className="warning-indicator" />
              <span className="warning-text">
                <strong>{t('landing.observationalSystem')}</strong> {t('landing.passiveWarning')}
              </span>
            </div>
          </div>

          {/* Right: Visual */}
          <div className="hero-visual-frame uts-hero-frame">
            <UnidirectionalThreatStream />
          </div>
        </div>
      </section>

      {/* Trust Strip */}
      <section className="landing-trust-strip scroll-reveal">
        <div className="trust-strip-container">
          <div className="trust-item">
            <span className="trust-label">{t('landing.trustPassive')}</span>
            <span className="trust-sub">{t('landing.trustPassiveSub')}</span>
          </div>
          <div className="trust-item">
            <span className="trust-label">{t('landing.trustMetadata')}</span>
            <span className="trust-sub">{t('landing.trustMetadataSub')}</span>
          </div>
          <div className="trust-item">
            <span className="trust-label">{t('landing.trustRealtime')}</span>
            <span className="trust-sub">{t('landing.trustRealtimeSub')}</span>
          </div>
          <div className="trust-item">
            <span className="trust-label">{t('landing.trustAnalyst')}</span>
            <span className="trust-sub">{t('landing.trustAnalystSub')}</span>
          </div>
        </div>
      </section>

      {/* Problem vs Approach Section */}
      <section className="landing-problem-approach scroll-reveal">
        <div className="landing-section-container">
          <div className="grid-2-col">
            <div className="problem-panel">
              <div className="section-eyebrow">{t('landing.problemEyebrow')}</div>
              <h2 className="section-title-sm">{t('landing.problemTitle')}</h2>
              <p className="section-body-text">
                {t('landing.problemText')}
              </p>
            </div>
            <div className="approach-panel">
              <div className="section-eyebrow">{t('landing.approachEyebrow')}</div>
              <h2 className="section-title-sm">{t('landing.approachTitle')}</h2>
              <p className="section-body-text">
                {t('landing.approachText')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Capability Section */}
      <section className="landing-capabilities scroll-reveal">
        <div className="landing-section-container">
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-10)' }}>
            <div className="section-eyebrow">{t('landing.capEyebrow')}</div>
            <h2 className="section-title">{t('landing.capTitle')}</h2>
            <p className="section-subtitle">
              {t('landing.capSubtitle')}
            </p>
          </div>

          <div className="capabilities-grid">
            {CAPABILITIES.map((cap) => (
              <div className="cap-card" key={cap.title}>
                <div className="cap-card-border-glow" />
                <div className="cap-card-header">
                  <div className="cap-technical-marker">{t('landing.signalSelector')}</div>
                  <h3 className="cap-title">{cap.title}</h3>
                </div>
                <p className="cap-desc">{cap.desc}</p>
                <div className="cap-meta">
                  <span className="cap-meta-label">{t('landing.inputData')}</span>
                  <span className="cap-meta-value mono">{cap.signal}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Simplified Detection Pipeline */}
      <section className="landing-pipeline scroll-reveal">
        <div className="landing-section-container">
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-10)' }}>
            <div className="section-eyebrow">{t('landing.pipelineEyebrow')}</div>
            <h2 className="section-title">{t('landing.pipelineTitle')}</h2>
            <p className="section-subtitle">
              {t('landing.pipelineSubtitle')}
            </p>
          </div>

          <div className="pipeline-container">
            {PIPELINE_STAGES.map((stage) => (
              <div key={stage.step} className="pipeline-step">
                <div className="pipeline-badge mono">{stage.step}</div>
                <h3 className="pipeline-name">{stage.name}</h3>
                <p className="pipeline-desc">{stage.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Evidence Alert Preview Section */}
      <section className="landing-preview scroll-reveal">
        <div className="landing-section-container">
          <div className="grid-2-col" style={{ alignItems: 'center', gap: 'var(--space-12)' }}>
            <div>
              <div className="section-eyebrow">{t('landing.previewEyebrow')}</div>
              <h2 className="section-title-sm">{t('landing.previewTitle')}</h2>
              <p className="section-body-text" style={{ marginBottom: 'var(--space-5)' }}>
                {t('landing.previewText')}
              </p>
              <Link to="/documentation" className="btn btn-ghost">
                {t('landing.readAlertModel')}
              </Link>
            </div>

            {/* Mock Alert Preview Card */}
            <div className="preview-alert-card">
              <div className="preview-alert-header">
                <div className="preview-alert-title-row">
                  <span className="mono preview-alert-id">ALT-004182</span>
                  <span className="severity-badge critical">{t('landing.critical')}</span>
                </div>
                <h3 className="preview-threat-label">{t('landing.volumetricDdos')}</h3>
              </div>
              <div className="preview-alert-body">
                <div className="preview-grid-mini">
                  <div>
                    <span className="mini-label">{t('landing.source')}</span>
                    <span className="mini-value mono">192.168.24.17</span>
                  </div>
                  <div>
                    <span className="mini-label">{t('landing.destination')}</span>
                    <span className="mini-value mono">10.42.8.21:443</span>
                  </div>
                  <div>
                    <span className="mini-label">{t('landing.confidence')}</span>
                    <span className="mini-value mono" style={{ color: 'var(--severity-critical)' }}>96.0%</span>
                  </div>
                  <div>
                    <span className="mini-label">{t('landing.workflowStatus')}</span>
                    <span className="mini-value mono" style={{ color: 'var(--status-new)' }}>{t('landing.new')}</span>
                  </div>
                </div>
                <div className="preview-evidence">
                  <span className="mini-label">{t('landing.evidenceObserved')}</span>
                  <p className="evidence-text">
                    {t('landing.evidenceText')}
                  </p>
                </div>
                <div className="preview-phase">
                  <span className="phase-badge live">{t('landing.liveMode')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── More about Vibhinetra — Deep Dive Section ── */}
      <section className="landing-deep-dive scroll-reveal">
        <div className="landing-section-container">
          <div className="deep-dive-toggle-area">
            <button
              className={`deep-dive-trigger ${deepDiveOpen ? 'open' : ''}`}
              onClick={() => setDeepDiveOpen(!deepDiveOpen)}
              aria-expanded={deepDiveOpen}
            >
              <div className="deep-dive-trigger-content">
                <div className="deep-dive-trigger-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 16v-4" />
                    <path d="M12 8h.01" />
                  </svg>
                </div>
                <div className="deep-dive-trigger-text">
                  <span className="deep-dive-trigger-label">{t('landing.deepDiveLabel')}</span>
                  <span className="deep-dive-trigger-sub">{t('landing.deepDiveSub')}</span>
                </div>
              </div>
              <svg className="deep-dive-chevron" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>
          </div>

          <div className={`deep-dive-content ${deepDiveOpen ? 'expanded' : ''}`}>
            {/* Threat Intelligence Deep Dive */}
            <div className="deep-dive-block">
              <div className="deep-dive-block-header">
                <div className="section-eyebrow">{t('landing.threatIntelEyebrow')}</div>
                <h3 className="deep-dive-block-title">{t('landing.threatIntelTitle')}</h3>
                <p className="deep-dive-block-desc">
                  {t('landing.threatIntelDesc')}
                </p>
              </div>

              <div className="deep-dive-threat-grid">
                {THREAT_DEEP_DIVE.map((threat) => (
                  <div key={threat.label} className="deep-dive-threat-card">
                    <h4 className="deep-dive-card-title">{threat.label}</h4>
                    <p className="deep-dive-card-desc">{threat.description}</p>
                    <div className="deep-dive-indicators">
                      <span className="deep-dive-indicators-label">{t('landing.keyIndicators')}</span>
                      <ul className="deep-dive-indicator-list">
                        {threat.indicators.map((ind) => (
                          <li key={ind}>{ind}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Detection Deep Dive */}
            <div className="deep-dive-block">
              <div className="deep-dive-block-header">
                <div className="section-eyebrow">{t('landing.aiDetectionEyebrow')}</div>
                <h3 className="deep-dive-block-title">{t('landing.aiDetectionTitle')}</h3>
                <p className="deep-dive-block-desc">
                  {t('landing.aiDetectionDesc')}
                </p>
              </div>

              <div className="deep-dive-detector-grid">
                {DETECTOR_DEEP_DIVE.map((det) => (
                  <div key={det.label} className="deep-dive-detector-card">
                    <h4 className="deep-dive-card-title">{det.label}</h4>
                    <p className="deep-dive-card-desc">{det.description}</p>
                    <div className="deep-dive-detector-meta">
                      <div className="deep-dive-detector-field">
                        <span className="deep-dive-field-label">{t('landing.classifiedThreats')}</span>
                        <div className="deep-dive-tags">
                          {det.threats.map((thr) => (
                            <span key={thr} className="deep-dive-tag">{thr}</span>
                          ))}
                        </div>
                      </div>
                      <div className="deep-dive-detector-field">
                        <span className="deep-dive-field-label">{t('landing.detectionMethod')}</span>
                        <span className="mono deep-dive-method">{det.method}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="landing-cta scroll-reveal">
        <div className="landing-section-container" style={{ textAlign: 'center' }}>
          <h2 className="cta-headline">{t('landing.ctaHeadline')}</h2>
          <p className="cta-sub">
            {t('landing.ctaSub')}
          </p>
          <div className="cta-actions">
            <Link to="/login" className="btn btn-primary btn-lg">
              {t('common.explorePlatform')}
            </Link>
            <Link to="/architecture" className="btn btn-ghost btn-lg">
              {t('common.viewArchitecture')}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
