/**
 * DiodeFlowVisualizer — Simplex Data-Diode Flow Dynamics Visualizer
 *
 * Simulates active telemetry ingestion across the hardware boundary.
 */

import { useEffect, useRef, useState } from 'react';
import './DiodeFlowVisualizer.css';

interface DiodeFlowVisualizerProps {
  realOpticalRate?: number;
}

export function DiodeFlowVisualizer({ realOpticalRate }: DiodeFlowVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [mockRate, setMockRate] = useState(0);

  const opticalRate = realOpticalRate !== undefined ? realOpticalRate : mockRate;

  // Main active drawing loop
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

    // Particle system for optical flow
    interface Packet {
      x: number;
      speed: number;
      length: number;
      alpha: number;
      laneOffset: number;
      color: string;
    }
    let packets: Packet[] = [];
    
    // Telemetry rate update loop for mock mode
    const rateInterval = setInterval(() => {
      setMockRate(Math.floor(Math.random() * 450) + 120);
    }, 1000);

    let animationFrameId: number;

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

      // Main fiber trunk line
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.lineWidth = 14;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(30, centerY);
      ctx.lineTo(width - 30, centerY);
      ctx.stroke();

      // Optical core glow
      ctx.strokeStyle = 'rgba(88, 199, 176, 0.15)';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(30, centerY);
      ctx.lineTo(width - 30, centerY);
      ctx.stroke();

      // Spawn new packets
      if (Math.random() > 0.3) {
        packets.push({
          x: 30,
          speed: Math.random() * 4 + 4,
          length: Math.random() * 20 + 10,
          alpha: Math.random() * 0.5 + 0.5,
          laneOffset: (Math.random() - 0.5) * 6, // Spread within the 14px trunk
          color: Math.random() > 0.1 ? 'rgba(88, 199, 176, ' : 'rgba(255, 147, 87, '
        });
      }

      // Draw and update packets
      for (let i = packets.length - 1; i >= 0; i--) {
        const p = packets[i];
        
        ctx.strokeStyle = p.color + p.alpha + ')';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(p.x, centerY + p.laneOffset);
        ctx.lineTo(p.x - p.length, centerY + p.laneOffset);
        ctx.stroke();

        // If passing the tap, spawn a mirrored packet going down
        if (p.x < sensorTapX && p.x + p.speed >= sensorTapX && Math.random() > 0.5) {
          // Draw tap flash
          ctx.fillStyle = 'rgba(126, 168, 216, 0.8)';
          ctx.beginPath();
          ctx.arc(sensorTapX, centerY, 3, 0, Math.PI * 2);
          ctx.fill();
        }

        p.x += p.speed;
        
        if (p.x - p.length > width) {
          packets.splice(i, 1);
        }
      }

      // ----------------------------------------------------
      // 2. Draw Vibhinetra Passive Splitter Tap (Mirror to Zeek)
      // ----------------------------------------------------
      const tapTargetY = height - 25;
      ctx.strokeStyle = 'rgba(126, 168, 216, 0.3)';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      
      // Animate dash offset for flow effect
      ctx.lineDashOffset = -(Date.now() / 40) % 8;
      
      ctx.beginPath();
      ctx.moveTo(sensorTapX, centerY);
      ctx.bezierCurveTo(sensorTapX + 20, centerY + 30, sensorTapX + 10, tapTargetY - 15, sensorTapX + 40, tapTargetY);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.lineDashOffset = 0;

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
      ctx.fillText('⚡ VIBHINETRA PASSIVE TAP', sensorBoxX + 10, sensorBoxY + 14);
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
      // Pulse effect based on time
      const pulse = (Math.sin(Date.now() / 200) + 1) / 2;
      const alphaInner = 0.6 + (pulse * 0.4);
      
      grad.addColorStop(0, 'rgba(255, 147, 87, 0.1)');
      grad.addColorStop(0.5, `rgba(255, 147, 87, ${alphaInner})`);
      grad.addColorStop(1, 'rgba(255, 147, 87, 0.1)');

      ctx.strokeStyle = grad;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(diodeX, barrierTopY);
      ctx.lineTo(diodeX, barrierTopY + barrierH);
      ctx.stroke();

      // Photodiode symbol
      ctx.fillStyle = `rgba(255, 147, 87, ${0.8 + pulse * 0.2})`;
      ctx.beginPath();
      ctx.arc(diodeX, centerY, 5, 0, Math.PI * 2);
      ctx.fill();

      // Physical direction arrows
      ctx.fillStyle = 'rgba(255, 147, 87, 0.9)';
      ctx.font = '11px sans-serif';
      ctx.fillText('▶', diodeX + 8, centerY + 4);

      // Reverse blocked indicator
      ctx.fillStyle = 'rgba(255, 92, 108, 0.8)';
      ctx.font = '9px "Fira Code", monospace';
      ctx.fillText('⮜ REVERSE RX: 0 BPS (SEVERED)', diodeX - 175, centerY - 28);

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      clearInterval(rateInterval);
    };
  }, []);

  return (
    <div className="diode-visualizer-card" ref={containerRef}>
      {/* Header Bar */}
      <div className="diode-card-header">
        <div className="diode-header-title-group">
          <div className="diode-pulse-beacon" style={{ opacity: 1, backgroundColor: 'var(--severity-info)' }} />
          <span className="diode-title">
            Hardware Data-Diode Simplex Flow Dynamics
          </span>
          <span className="demo-badge" style={{ background: 'var(--severity-info)', color: '#fff', borderColor: 'var(--severity-info)' }}>
            LIVE TELEMETRY
          </span>
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

        {/* Canvas - Active State */}
        <canvas
          ref={canvasRef}
          className="diode-canvas"
        />

        {/* Active Scenario Indicator Banner */}
        <div className="diode-scenario-banner" style={{ justifyContent: 'center', borderColor: 'var(--severity-info)' }}>
          <span style={{ color: 'var(--severity-info)' }}>
            ACTIVE: Ingesting raw network flow via simplex physical layer at ~{opticalRate} Mbps.
          </span>
        </div>
      </div>

      {/* Hardware Telemetry Strip */}
      <div className="diode-telemetry-bar">
        <div className="diode-metric-item">
          <span className="diode-metric-dot" style={{ backgroundColor: 'var(--severity-info)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Optical Link:</span>
          <span className="diode-metric-val" style={{ color: 'var(--severity-info)' }}>LOCKED (Class 1 Laser)</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" style={{ backgroundColor: '#FF5C6C' }} />
          <span style={{ color: 'var(--text-muted)' }}>Reverse Channel:</span>
          <span className="diode-metric-val" style={{ color: '#FF5C6C' }}>0 bps (Physically Isolated)</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" style={{ backgroundColor: 'var(--severity-info)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Optical Splitter Tap:</span>
          <span className="diode-metric-val" style={{ color: 'var(--text-primary)' }}>90/10 Split (0.8 dB Loss)</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" style={{ backgroundColor: 'var(--severity-info)' }} />
          <span style={{ color: 'var(--text-muted)' }}>Monitored Rate:</span>
          <span className="diode-metric-val" style={{ color: 'var(--text-primary)' }}>{(opticalRate * 0.1).toFixed(1)} Mbps</span>
        </div>

        <span className="diode-sim-badge">
          PASSIVE READ-ONLY COMPLIANT
        </span>
      </div>
    </div>
  );
}
