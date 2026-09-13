/**
 * DiodeFlowVisualizer — Simplex Data-Diode Flow Dynamics Visualizer
 *
 * Modified for Phase 5: Removed fake packet simulation.
 * Now acts as a truthful, static idle state representing the hardware boundary
 * while awaiting actual telemetry ingestion.
 */

import { useEffect, useRef } from 'react';
import './DiodeFlowVisualizer.css';

export function DiodeFlowVisualizer() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Main idle drawing loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Resize handling with devicePixelRatio
    const handleResize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      const rect = parent.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = 240 * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = '240px';
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    const render = () => {
      const width = canvas.width / (window.devicePixelRatio || 1);
      const height = 240;

      // Clear canvas
      ctx.fillStyle = 'rgba(15, 17, 22, 1)';
      ctx.fillRect(0, 0, width, height);

      // Boundaries & landmark positions
      const enclaveEndX = width * 0.30;
      const diodeX = width * 0.45;
      const sensorTapX = width * 0.65;
      const centerY = height * 0.45;

      // ----------------------------------------------------
      // 1. Draw Optical Waveguide / Simplex Fiber Bus
      // ----------------------------------------------------
      // Subtle Enclave perimeter demarcation
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 4]);
      ctx.beginPath();
      ctx.moveTo(enclaveEndX, 25);
      ctx.lineTo(enclaveEndX, height - 25);
      ctx.stroke();
      ctx.setLineDash([]);

      // Main fiber trunk line (idle)
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 14;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(30, centerY);
      ctx.lineTo(width - 30, centerY);
      ctx.stroke();

      // Optical core glow (faint)
      ctx.strokeStyle = 'rgba(88, 199, 176, 0.05)';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(30, centerY);
      ctx.lineTo(width - 30, centerY);
      ctx.stroke();

      // ----------------------------------------------------
      // 2. Draw Irochi Passive Splitter Tap (Mirror to Zeek)
      // ----------------------------------------------------
      const tapTargetY = height - 25;
      ctx.strokeStyle = 'rgba(126, 168, 216, 0.15)';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(sensorTapX, centerY);
      ctx.bezierCurveTo(sensorTapX + 20, centerY + 30, sensorTapX + 10, tapTargetY - 15, sensorTapX + 40, tapTargetY);
      ctx.stroke();
      ctx.setLineDash([]);

      // Passive Sensor Module Box
      ctx.fillStyle = 'rgba(26, 32, 44, 0.9)';
      ctx.strokeStyle = '#7EA8D8';
      ctx.lineWidth = 1.5;
      const sensorBoxW = 160;
      const sensorBoxH = 26;
      const sensorBoxX = sensorTapX + 40;
      const sensorBoxY = tapTargetY - 13;

      ctx.beginPath();
      ctx.roundRect(sensorBoxX, sensorBoxY, sensorBoxW, sensorBoxH, 6);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#7EA8D8';
      ctx.font = '10px "Fira Code", monospace';
      ctx.fillText('⚡ IROCHI PASSIVE TAP', sensorBoxX + 10, sensorBoxY + 14);
      ctx.fillStyle = '#A0AEC0';
      ctx.font = '8px "Fira Code", monospace';
      ctx.fillText('10% Split · 0 Inline Latency', sensorBoxX + 10, sensorBoxY + 23);

      // ----------------------------------------------------
      // 3. Draw Hardware Data Diode Optical Barrier
      // ----------------------------------------------------
      const barrierH = 120;
      const barrierTopY = centerY - barrierH / 2;

      // Vertical optical gate boundary
      const grad = ctx.createLinearGradient(diodeX, barrierTopY, diodeX, barrierTopY + barrierH);
      grad.addColorStop(0, 'rgba(255, 147, 87, 0.1)');
      grad.addColorStop(0.5, 'rgba(255, 147, 87, 0.5)');
      grad.addColorStop(1, 'rgba(255, 147, 87, 0.1)');

      ctx.strokeStyle = grad;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(diodeX, barrierTopY);
      ctx.lineTo(diodeX, barrierTopY + barrierH);
      ctx.stroke();

      // Photodiode symbol
      ctx.fillStyle = 'rgba(255, 147, 87, 0.5)';
      ctx.beginPath();
      ctx.arc(diodeX, centerY, 5, 0, Math.PI * 2);
      ctx.fill();

      // Physical direction arrows
      ctx.fillStyle = 'rgba(255, 147, 87, 0.5)';
      ctx.font = '11px sans-serif';
      ctx.fillText('▶', diodeX + 8, centerY + 4);

      // Reverse blocked indicator
      ctx.fillStyle = 'rgba(255, 92, 108, 0.5)';
      ctx.font = '9px "Fira Code", monospace';
      ctx.fillText('⮜ REVERSE RX: 0 BPS (SEVERED)', diodeX - 175, centerY - 28);
    };

    // Render once, no animation loop needed for static idle state
    render();

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className="diode-visualizer-card" ref={containerRef}>
      {/* Header Bar */}
      <div className="diode-card-header">
        <div className="diode-header-title-group">
          <div className="diode-pulse-beacon" style={{ opacity: 0.3 }} />
          <span className="diode-title">
            Hardware Data-Diode Simplex Flow Dynamics
          </span>
          <span className="demo-badge">AWAITING INGESTION</span>
        </div>
      </div>

      {/* Stage Area */}
      <div className="diode-stage-wrapper">
        <div className="diode-stage-grid" />

        {/* Zone Labels Top Bar */}
        <div className="diode-zones-bar">
          <div className="diode-zone-header">
            <span className="diode-zone-name">ZONE 1: SENDER ENCLAVE</span>
            <span className="diode-zone-desc">10.0.4.0/24 Air-Gapped SCADA / Defense</span>
          </div>

          <div className="diode-zone-header barrier-zone">
            <span className="diode-zone-name">ZONE 2: HARDWARE DIODE</span>
            <span className="diode-zone-desc">Physical Laser TX → Photodiode Barrier</span>
          </div>

          <div className="diode-zone-header tap-zone">
            <span className="diode-zone-name">ZONE 3: PASSIVE OPTICAL TAP</span>
            <span className="diode-zone-desc">10% Split Mirror → Zeek Normalizer</span>
          </div>

          <div className="diode-zone-header dst-zone">
            <span className="diode-zone-name">ZONE 4: DESTINATION HISTORIAN</span>
            <span className="diode-zone-desc">198.51.100.0/24 Replicated Database</span>
          </div>
        </div>

        {/* Canvas - Idle State */}
        <canvas
          ref={canvasRef}
          className="diode-canvas"
        />

        {/* Active Scenario Indicator Banner */}
        <div className="diode-scenario-banner" style={{ justifyContent: 'center' }}>
          <span style={{ color: 'var(--text-muted)' }}>
            IDLE: Awaiting backend telemetry ingestion stream.
          </span>
        </div>
      </div>

      {/* Hardware Telemetry Strip */}
      <div className="diode-telemetry-bar">
        <div className="diode-metric-item">
          <span className="diode-metric-dot" style={{ backgroundColor: 'var(--text-muted)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Optical Link:</span>
          <span className="diode-metric-val" style={{ color: 'var(--text-muted)' }}>Unavailable</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" style={{ backgroundColor: 'var(--text-muted)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Reverse Channel:</span>
          <span className="diode-metric-val" style={{ color: '#FF5C6C' }}>0 bps (Physically Isolated)</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" style={{ backgroundColor: 'var(--text-muted)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Optical Splitter Tap:</span>
          <span className="diode-metric-val" style={{ color: 'var(--text-muted)' }}>90/10 Split (0.8 dB Loss)</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" style={{ backgroundColor: 'var(--text-muted)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Monitored Rate:</span>
          <span className="diode-metric-val" style={{ color: 'var(--text-muted)' }}>Unavailable</span>
        </div>

        <span className="diode-sim-badge">
          PASSIVE READ-ONLY COMPLIANT
        </span>
      </div>
    </div>
  );
}
