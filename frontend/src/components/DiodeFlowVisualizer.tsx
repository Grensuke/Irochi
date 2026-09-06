/**
 * DiodeFlowVisualizer — Simplex Data-Diode Flow Dynamics Visualizer
 *
 * Visually depicts the physical boundary of unidirectional IP traffic:
 * Enclave Source -> [Physical Hardware Diode] -> [Irochi Passive Tap Sensor] -> Destination Network.
 *
 * Features:
 * - 60fps Canvas-animated simplex packet stream strictly flowing Left-to-Right.
 * - Hardware barrier with optical photodiode emitter/sensor and reverse block markers.
 * - Passive optical splitter tap duplicating packet energy to Irochi Zeek sensor.
 * - Interactive scenario testing (DDoS, C2, Exfil, DGA, Normal SCADA).
 * - Click/Hover packet inspector with simplex entropy and unacknowledged flow signals.
 * - Physical link telemetry indicator bar.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { Alert, ThreatType } from '../types';
import './DiodeFlowVisualizer.css';

interface PacketInfo {
  id: string;
  threatType: ThreatType | 'normal';
  src: string;
  dst: string;
  proto: string;
  bytes: number;
  entropy: number;
  signal: string;
  confidence: number;
}

interface Particle {
  id: string;
  x: number;
  y: number;
  vx: number;
  size: number;
  threatType: ThreatType | 'normal';
  color: string;
  alpha: number;
  isTapClone?: boolean;
  tapY?: number;
  tapVy?: number;
  info: PacketInfo;
}

type ScenarioMode = 'all' | 'ddos' | 'c2' | 'exfil' | 'dga' | 'normal';

interface DiodeFlowVisualizerProps {
  alerts?: Alert[];
  onSelectThreat?: (threat: ThreatType | 'all') => void;
}

const THREAT_COLORS: Record<string, string> = {
  volumetric_ddos: '#FF5C6C',      // Red
  c2_beaconing: '#C084FC',         // Purple/Violet
  data_exfiltration: '#FF9357',    // Orange
  dga_dns_tunnel: '#F2C94C',       // Amber
  recon_portscan: '#FBBF24',       // Yellow
  encrypted_malware: '#F43F5E',    // Rose
  normal: '#58C7B0',               // Teal/Emerald
};

const SCENARIO_NAMES: Record<ScenarioMode, string> = {
  all: 'Live Stream (Mixed)',
  ddos: '⚡ DDoS Simplex Flood',
  c2: '📡 C2 Blind Beacon',
  exfil: '📦 Covert Exfiltration',
  dga: '🔍 DGA Tunnel Stream',
  normal: '🛡️ Benign SCADA Sync',
};

export function DiodeFlowVisualizer({ alerts }: DiodeFlowVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Interaction & state
  const [scenario, setScenario] = useState<ScenarioMode>('all');
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1);
  const [activePacket, setActivePacket] = useState<{ packet: PacketInfo; x: number; y: number } | null>(null);
  const [throughputMbps, setThroughputMbps] = useState<number>(42.8);
  const [packetsPerSec, setPacketsPerSec] = useState<number>(1840);

  // Particles array stored in ref for 60fps rendering without re-renders
  const particlesRef = useRef<Particle[]>([]);
  const animFrameRef = useRef<number>(0);
  const lastSpawnRef = useRef<number>(0);

  // Generate packet data for particle
  const createPacketData = useCallback((type: ThreatType | 'normal'): PacketInfo => {
    const id = `PKT-${Math.floor(100000 + Math.random() * 900000)}`;
    switch (type) {
      case 'volumetric_ddos':
        return {
          id,
          threatType: 'volumetric_ddos',
          src: `198.51.100.${Math.floor(2 + Math.random() * 250)}`,
          dst: '10.0.4.10:80',
          proto: 'UDP/SYN',
          bytes: 64,
          entropy: 3.12,
          signal: 'High-frequency unacknowledged burst; zero TCP handshake ACKs returned.',
          confidence: 0.94,
        };
      case 'c2_beaconing':
        return {
          id,
          threatType: 'c2_beaconing',
          src: '10.0.4.82',
          dst: '203.0.113.50:443',
          proto: 'TCP/TLS',
          bytes: 342,
          entropy: 6.84,
          signal: 'Strict 1.002s periodic interval; JA4 client hello without server response.',
          confidence: 0.88,
        };
      case 'data_exfiltration':
        return {
          id,
          threatType: 'data_exfiltration',
          src: '10.0.4.45',
          dst: '198.51.100.99:8443',
          proto: 'TCP/HTTPS',
          bytes: 1420,
          entropy: 7.94,
          signal: 'Simplex Outbound Volumetric Density anomaly; maximum chunk quantization.',
          confidence: 0.91,
        };
      case 'dga_dns_tunnel':
        return {
          id,
          threatType: 'dga_dns_tunnel',
          src: '10.0.4.15',
          dst: '10.0.4.1:53',
          proto: 'UDP/DNS',
          bytes: 198,
          entropy: 4.85,
          signal: 'High Shannon domain label entropy (x8k9j-v2.edge); TX-only DNS query spam.',
          confidence: 0.86,
        };
      default:
        return {
          id,
          threatType: 'normal',
          src: `10.0.4.${Math.floor(10 + Math.random() * 40)}`,
          dst: `198.51.100.${Math.floor(10 + Math.random() * 40)}`,
          proto: Math.random() > 0.5 ? 'TCP/OPC-UA' : 'UDP/Syslog',
          bytes: Math.floor(128 + Math.random() * 600),
          entropy: 4.2,
          signal: 'Compliant simplex telemetry synchronization; standard payload distribution.',
          confidence: 0.05,
        };
    }
  }, []);

  // Determine current spawn type based on active scenario
  const getNextThreatType = useCallback((): ThreatType | 'normal' => {
    if (scenario === 'ddos') return 'volumetric_ddos';
    if (scenario === 'c2') return 'c2_beaconing';
    if (scenario === 'exfil') return 'data_exfiltration';
    if (scenario === 'dga') return 'dga_dns_tunnel';
    if (scenario === 'normal') return 'normal';

    // Scenario 'all' / live: mix in recent alerts or random realistic distribution
    if (alerts && alerts.length > 0 && Math.random() < 0.45) {
      const picked = alerts[Math.floor(Math.random() * alerts.length)];
      if (picked && picked.threat_type) {
        return picked.threat_type;
      }
    }

    const rand = Math.random();
    if (rand < 0.65) return 'normal';
    if (rand < 0.75) return 'volumetric_ddos';
    if (rand < 0.83) return 'c2_beaconing';
    if (rand < 0.92) return 'data_exfiltration';
    return 'dga_dns_tunnel';
  }, [scenario, alerts]);

  // Instant scenario switcher with immediate particle injection and telemetry shifts
  const switchScenario = useCallback((mode: ScenarioMode) => {
    setScenario(mode);
    setActivePacket(null);

    // Immediate realistic metrics jump for the selected scenario
    switch (mode) {
      case 'ddos':
        setThroughputMbps(842.5);
        setPacketsPerSec(128400);
        break;
      case 'c2':
        setThroughputMbps(14.8);
        setPacketsPerSec(320);
        break;
      case 'exfil':
        setThroughputMbps(184.2);
        setPacketsPerSec(8950);
        break;
      case 'dga':
        setThroughputMbps(28.5);
        setPacketsPerSec(2410);
        break;
      case 'normal':
        setThroughputMbps(42.8);
        setPacketsPerSec(1840);
        break;
      case 'all':
      default:
        setThroughputMbps(56.4);
        setPacketsPerSec(2890);
        break;
    }

    // Instantly seed particles across the entire width of the canvas
    const canvas = canvasRef.current;
    const width = canvas ? (canvas.width / (window.devicePixelRatio || 1)) : 800;
    const centerY = 240 * 0.45;
    const threatToSpawn: ThreatType | 'normal' = 
      mode === 'ddos' ? 'volumetric_ddos' :
      mode === 'c2' ? 'c2_beaconing' :
      mode === 'exfil' ? 'data_exfiltration' :
      mode === 'dga' ? 'dga_dns_tunnel' :
      mode === 'normal' ? 'normal' : 'normal';

    const count = mode === 'ddos' ? 26 : 15;
    const newParticles: Particle[] = [];
    const step = (width - 80) / count;

    for (let i = 0; i < count; i++) {
      const type = mode === 'all' 
        ? (i % 3 === 0 ? 'volumetric_ddos' : i % 4 === 0 ? 'c2_beaconing' : 'normal')
        : threatToSpawn;
      const pInfo = createPacketData(type);
      const color = THREAT_COLORS[type] || '#58C7B0';
      const size = type === 'data_exfiltration' ? 7 : (type === 'volumetric_ddos' ? 5.5 : 4.5);
      const speed = (2.2 + Math.random() * 1.4) * speedMultiplier;

      newParticles.push({
        id: pInfo.id,
        x: 40 + i * step + (Math.random() - 0.5) * 15,
        y: centerY + (Math.random() - 0.5) * 12,
        vx: speed,
        size,
        threatType: type,
        color,
        alpha: 1,
        info: pInfo,
      });
    }

    particlesRef.current = newParticles;
  }, [createPacketData, speedMultiplier]);

  // Main animation loop
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

    const render = (time: number) => {
      const width = canvas.width / (window.devicePixelRatio || 1);
      const height = 240;

      // Clear canvas with subtle trail fade
      ctx.fillStyle = 'rgba(15, 17, 22, 0.28)';
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
      ctx.strokeStyle = 'rgba(88, 199, 176, 0.25)';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(30, centerY);
      ctx.lineTo(width - 30, centerY);
      ctx.stroke();

      // ----------------------------------------------------
      // 2. Draw Irochi Passive Splitter Tap (Mirror to Zeek)
      // ----------------------------------------------------
      const tapTargetY = height - 25;
      ctx.strokeStyle = 'rgba(126, 168, 216, 0.35)';
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
      // Photodiode Laser emitter / receiver icons
      const barrierH = 120;
      const barrierTopY = centerY - barrierH / 2;

      // Vertical optical gate boundary
      const grad = ctx.createLinearGradient(diodeX, barrierTopY, diodeX, barrierTopY + barrierH);
      grad.addColorStop(0, 'rgba(255, 147, 87, 0.1)');
      grad.addColorStop(0.5, '#FF9357');
      grad.addColorStop(1, 'rgba(255, 147, 87, 0.1)');

      ctx.strokeStyle = grad;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(diodeX, barrierTopY);
      ctx.lineTo(diodeX, barrierTopY + barrierH);
      ctx.stroke();

      // Photodiode symbol
      ctx.fillStyle = '#FF9357';
      ctx.beginPath();
      ctx.arc(diodeX, centerY, 5, 0, Math.PI * 2);
      ctx.fill();

      // Physical direction arrows
      ctx.fillStyle = 'rgba(255, 147, 87, 0.8)';
      ctx.font = '11px sans-serif';
      ctx.fillText('▶', diodeX + 8, centerY + 4);

      // Reverse blocked indicator
      ctx.fillStyle = 'rgba(255, 92, 108, 0.7)';
      ctx.font = '9px "Fira Code", monospace';
      ctx.fillText('⮜ REVERSE RX: 0 BPS (SEVERED)', diodeX - 175, centerY - 28);

      // ----------------------------------------------------
      // 4. Spawn New Packets based on rate & scenario
      // ----------------------------------------------------
      const spawnInterval = scenario === 'ddos' ? 45 : 160;
      if (isPlaying && time - lastSpawnRef.current > spawnInterval) {
        lastSpawnRef.current = time;

        const countToSpawn = scenario === 'ddos' ? 3 : 1;
        for (let i = 0; i < countToSpawn; i++) {
          const type = getNextThreatType();
          const pInfo = createPacketData(type);
          const color = THREAT_COLORS[type] || '#58C7B0';
          const size = type === 'data_exfiltration' ? 7 : (type === 'volumetric_ddos' ? 5.5 : 4.5);
          const speed = (2.2 + Math.random() * 1.4) * speedMultiplier;

          particlesRef.current.push({
            id: pInfo.id,
            x: 20 + Math.random() * 20,
            y: centerY + (Math.random() - 0.5) * 12,
            vx: speed,
            size,
            threatType: type,
            color,
            alpha: 1,
            info: pInfo,
          });
        }
      }

      // ----------------------------------------------------
      // 5. Update and Draw Particles
      // ----------------------------------------------------
      const nextParticles: Particle[] = [];

      for (let i = 0; i < particlesRef.current.length; i++) {
        const p = particlesRef.current[i];

        if (isPlaying) {
          // Normal horizontal movement
          if (!p.isTapClone) {
            p.x += p.vx;

            // When crossing Sensor Tap point, 10% chance to spawn a visual mirrored clone peeling down
            if (Math.abs(p.x - sensorTapX) < p.vx && Math.random() < 0.85) {
              nextParticles.push({
                ...p,
                id: `${p.id}-tap`,
                isTapClone: true,
                tapY: centerY,
                tapVy: 1.8 * speedMultiplier,
                size: p.size * 0.8,
                alpha: 0.8,
              });
            }
          } else {
            // Tap clone moving down along curve into sensor box
            p.x += p.vx * 0.4;
            p.tapY = (p.tapY || centerY) + (p.tapVy || 1.8);
          }
        }

        const currY = p.isTapClone ? (p.tapY || centerY) : p.y;

        // Draw particle tail / motion streak
        ctx.strokeStyle = p.color;
        ctx.lineWidth = p.size;
        ctx.globalAlpha = p.isTapClone ? 0.45 : 0.85;
        ctx.beginPath();
        ctx.moveTo(p.x - p.vx * 3, currY);
        ctx.lineTo(p.x, currY);
        ctx.stroke();

        // Draw particle core
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, currY, p.size, 0, Math.PI * 2);
        ctx.fill();

        // Extra halo for high-severity threats
        if (p.threatType !== 'normal' && !p.isTapClone) {
          ctx.strokeStyle = p.color;
          ctx.lineWidth = 1.2;
          ctx.globalAlpha = 0.5;
          ctx.beginPath();
          ctx.arc(p.x, currY, p.size + 4, 0, Math.PI * 2);
          ctx.stroke();
        }

        ctx.globalAlpha = 1;

        // Keep particle if within canvas bounds
        const isAlive = p.isTapClone
          ? (currY < tapTargetY + 10 && p.x < width)
          : (p.x < width - 20);

        if (isAlive) {
          nextParticles.push(p);
        }
      }

      particlesRef.current = nextParticles;

      // Continue animation loop
      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('resize', handleResize);
    };
  }, [isPlaying, speedMultiplier, scenario, getNextThreatType, createPacketData]);

  // Handle canvas mouse hover / click to inspect packets
  const handleCanvasInteraction = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    // Find closest particle within 16px radius
    let found: Particle | null = null;
    let minDist = 20;

    for (const p of particlesRef.current) {
      const py = p.isTapClone ? (p.tapY || 108) : p.y;
      const d = Math.hypot(p.x - mx, py - my);
      if (d < minDist) {
        minDist = d;
        found = p;
      }
    }

    if (found) {
      setActivePacket({
        packet: found.info,
        x: Math.min(rect.width - 290, Math.max(10, found.x - 60)),
        y: Math.min(180, Math.max(20, found.y - 40)),
      });
    } else if (e.type === 'click') {
      setActivePacket(null);
    }
  };

  // Dynamic telemetry throughput jitter for visual realism
  useEffect(() => {
    const interval = setInterval(() => {
      setThroughputMbps((prev) => +(prev + (Math.random() - 0.48) * 1.8).toFixed(1));
      setPacketsPerSec((prev) => Math.max(900, Math.round(prev + (Math.random() - 0.48) * 60)));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="diode-visualizer-card" ref={containerRef}>
      {/* Header Bar */}
      <div className="diode-card-header">
        <div className="diode-header-title-group">
          <div className="diode-pulse-beacon" />
          <span className="diode-title">
            Hardware Data-Diode Simplex Flow Dynamics
          </span>
          <span className="demo-badge">REAL-TIME SIMPLEX OPTICAL TAP</span>
        </div>

        {/* Interactive Scenario Buttons */}
        <div className="diode-controls">
          {(['all', 'ddos', 'c2', 'exfil', 'dga', 'normal'] as ScenarioMode[]).map((mode) => (
            <button
              key={mode}
              className={`diode-scenario-btn ${scenario === mode ? 'active' : ''}`}
              onClick={() => switchScenario(mode)}
            >
              {SCENARIO_NAMES[mode]}
            </button>
          ))}

          <div style={{ width: '1px', height: '18px', background: 'var(--border-subtle)', margin: '0 4px' }} />

          {/* Speed & Play/Pause */}
          <button
            className="diode-action-btn"
            onClick={() => setSpeedMultiplier((prev) => (prev === 1 ? 2 : 1))}
            title="Toggle playback speed"
          >
            {speedMultiplier}x
          </button>
          <button
            className="diode-action-btn"
            onClick={() => setIsPlaying((prev) => !prev)}
            title={isPlaying ? 'Pause animation' : 'Resume animation'}
          >
            {isPlaying ? '⏸' : '▶'}
          </button>
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

        {/* Canvas Animation */}
        <canvas
          ref={canvasRef}
          className="diode-canvas"
          onMouseMove={handleCanvasInteraction}
          onClick={handleCanvasInteraction}
        />

        {/* Active Scenario Indicator Banner */}
        <div className="diode-scenario-banner">
          <div 
            className="diode-scenario-banner-dot" 
            style={{ 
              backgroundColor: scenario === 'normal' ? '#58C7B0' : 
                scenario === 'all' ? '#7EA8D8' : 
                THREAT_COLORS[scenario === 'ddos' ? 'volumetric_ddos' : scenario === 'c2' ? 'c2_beaconing' : scenario === 'exfil' ? 'data_exfiltration' : 'dga_dns_tunnel'] || '#58C7B0'
            }} 
          />
          <span>
            {scenario === 'ddos' && 'SIMULATING: Volumetric DDoS Simplex Flood (Unsolicited SYN/UDP Swarm)'}
            {scenario === 'c2' && 'SIMULATING: Botnet C2 Blind Beaconing (Fixed 1.002s Periodicity)'}
            {scenario === 'exfil' && 'SIMULATING: Covert Exfiltration (High-Entropy Block Stream)'}
            {scenario === 'dga' && 'SIMULATING: DGA / DNS Tunneling (Algorithmic Query Spam)'}
            {scenario === 'normal' && 'BASELINE: Compliant Simplex SCADA Telemetry (Zero Anomalies)'}
            {scenario === 'all' && 'MONITORING: Passive Multi-Threat Ingestion Stream'}
          </span>
        </div>

        {/* Hover / Click Inspection Popover */}
        {activePacket && (
          <div
            className="diode-inspector-card"
            style={{ left: `${activePacket.x}px`, top: `${activePacket.y}px` }}
          >
            <div className="diode-inspector-header">
              <span
                className="diode-inspector-type"
                style={{ color: THREAT_COLORS[activePacket.packet.threatType] || '#58C7B0' }}
              >
                {activePacket.packet.threatType.replace(/_/g, ' ').toUpperCase()}
              </span>
              <button
                className="diode-inspector-close"
                onClick={() => setActivePacket(null)}
                aria-label="Close packet inspector"
              >
                ×
              </button>
            </div>

            <div className="diode-inspector-row">
              <span className="diode-inspector-key">Packet ID</span>
              <span className="diode-inspector-val">{activePacket.packet.id}</span>
            </div>
            <div className="diode-inspector-row">
              <span className="diode-inspector-key">Flow Path</span>
              <span className="diode-inspector-val">{activePacket.packet.src} → {activePacket.packet.dst}</span>
            </div>
            <div className="diode-inspector-row">
              <span className="diode-inspector-key">Protocol / Size</span>
              <span className="diode-inspector-val">{activePacket.packet.proto} ({activePacket.packet.bytes} B)</span>
            </div>
            <div className="diode-inspector-row">
              <span className="diode-inspector-key">Shannon Entropy</span>
              <span className="diode-inspector-val">{activePacket.packet.entropy} / 8.00 bits</span>
            </div>
            <div className="diode-inspector-row">
              <span className="diode-inspector-key">Detector Confidence</span>
              <span className="diode-inspector-val">{(activePacket.packet.confidence * 100).toFixed(0)}%</span>
            </div>

            <div className="diode-simplex-evidence">
              <strong>Simplex Telemetry Evidence:</strong> {activePacket.packet.signal}
            </div>
          </div>
        )}
      </div>

      {/* Hardware Telemetry Strip */}
      <div className="diode-telemetry-bar">
        <div className="diode-metric-item">
          <span className="diode-metric-dot" />
          <span>Optical Link:</span>
          <span className="diode-metric-val">1.25 Gbps Simplex</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" />
          <span>Reverse Channel:</span>
          <span className="diode-metric-val" style={{ color: '#FF5C6C' }}>0 bps (Physically Isolated)</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" />
          <span>Optical Splitter Tap:</span>
          <span className="diode-metric-val">90/10 Split (0.8 dB Loss)</span>
        </div>

        <div className="diode-metric-item">
          <span className="diode-metric-dot" />
          <span>Monitored Rate:</span>
          <span className="diode-metric-val">{throughputMbps} Mbps (~{packetsPerSec} pps)</span>
        </div>

        <span className="diode-sim-badge">
          PASSIVE READ-ONLY COMPLIANT
        </span>
      </div>
    </div>
  );
}
