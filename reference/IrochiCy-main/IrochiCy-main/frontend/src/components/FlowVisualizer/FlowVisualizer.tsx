import { useState, useEffect, useRef, useCallback } from 'react';
import { generateNetworkFlows } from '@/mocks/mockService';
import type { NetworkFlow, ThreatType } from '@/types';

const THREAT_COLORS: Record<ThreatType | 'normal', string> = {
  ddos: '#FF3B5C', recon: '#FF7A2F', dns: '#A78BFA', tls: '#5B8CFF', exfil: '#F5C518', normal: '#505A68',
};

interface FlowVisualizerProps { speed: number; paused: boolean; }

interface AnimatedLine {
  id: string; x1: number; y1: number; x2: number; y2: number;
  color: string; thickness: number; suspicious: boolean; progress: number; opacity: number;
  srcLabel: string; dstLabel: string;
}

export default function FlowVisualizer({ speed, paused }: FlowVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const linesRef = useRef<AnimatedLine[]>([]);
  const animFrameRef = useRef<number>(0);
  const [dims, setDims] = useState({ w: 800, h: 340 });

  // Handle resize
  useEffect(() => {
    const parent = canvasRef.current?.parentElement;
    if (!parent) return;
    const obs = new ResizeObserver(entries => {
      const { width } = entries[0].contentRect;
      setDims({ w: width, h: 340 });
    });
    obs.observe(parent);
    return () => obs.disconnect();
  }, []);

  // Generate new flows on tick
  useEffect(() => {
    if (paused) return;
    const interval = setInterval(() => {
      const flows = generateNetworkFlows(Math.floor(5 + Math.random() * 10));
      const newLines: AnimatedLine[] = flows.map((f: NetworkFlow) => {
        const srcZone = dims.w * 0.15;
        const dstZone = dims.w * 0.85;
        return {
          id: f.id,
          x1: srcZone + Math.random() * 40 - 20,
          y1: 30 + Math.random() * (dims.h - 60),
          x2: dstZone + Math.random() * 40 - 20,
          y2: 30 + Math.random() * (dims.h - 60),
          color: THREAT_COLORS[f.event_type],
          thickness: Math.max(1, Math.min(4, f.bytes_sent / 250000)),
          suspicious: f.suspicious,
          progress: 0,
          opacity: 1,
          srcLabel: f.src_ip.split('.').slice(-1)[0],
          dstLabel: f.dst_ip.split('.').slice(-1)[0],
        };
      });
      linesRef.current = [...linesRef.current.filter(l => l.opacity > 0.05), ...newLines];
    }, 2000 / speed);
    return () => clearInterval(interval);
  }, [speed, paused, dims]);

  // Animation loop
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, dims.w, dims.h);

    // Background zones
    ctx.fillStyle = 'rgba(0,194,168,0.04)';
    ctx.fillRect(0, 0, dims.w * 0.25, dims.h);
    ctx.fillStyle = 'rgba(91,140,255,0.04)';
    ctx.fillRect(dims.w * 0.75, 0, dims.w * 0.25, dims.h);

    // Labels
    ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#6B7280';
    ctx.textAlign = 'center';
    ctx.fillText('SOURCE', dims.w * 0.12, 18);
    ctx.fillText('DESTINATION', dims.w * 0.88, 18);

    // Update and draw lines
    for (const line of linesRef.current) {
      if (!paused) {
        line.progress = Math.min(1, line.progress + 0.015 * speed);
        if (line.progress >= 1) {
          line.opacity = Math.max(0, line.opacity - 0.02 * speed);
        }
      }

      const { x1, y1, x2, y2, color, thickness, suspicious, progress, opacity } = line;
      const cx = x1 + (x2 - x1) * progress;
      const cy = y1 + (y2 - y1) * progress;

      // Line
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(cx, cy);
      ctx.strokeStyle = color;
      ctx.globalAlpha = opacity * 0.6;
      ctx.lineWidth = thickness;
      ctx.stroke();
      ctx.globalAlpha = 1;

      // Src dot
      ctx.beginPath();
      ctx.arc(x1, y1, 3, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = opacity;
      ctx.fill();

      // Head dot
      if (progress < 1) {
        ctx.beginPath();
        ctx.arc(cx, cy, 2 + thickness, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = opacity * 0.8;
        ctx.fill();
      }

      // Dst dot when arrived
      if (progress >= 0.95) {
        ctx.beginPath();
        ctx.arc(x2, y2, 3, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = opacity;
        ctx.fill();
      }

      // Suspicious warning
      if (suspicious && progress > 0.3 && progress < 0.8) {
        ctx.font = 'bold 12px sans-serif';
        ctx.fillStyle = '#FF3B5C';
        ctx.globalAlpha = opacity;
        ctx.fillText('⚠', cx + 6, cy - 6);
      }

      ctx.globalAlpha = 1;
    }

    // Clean up dead lines
    linesRef.current = linesRef.current.filter(l => l.opacity > 0.01);
    animFrameRef.current = requestAnimationFrame(draw);
  }, [dims, speed, paused]);

  useEffect(() => {
    animFrameRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [draw]);

  return (
    <canvas
      ref={canvasRef}
      width={dims.w}
      height={dims.h}
      style={{ width: '100%', height: '340px', borderRadius: 'var(--radius-md)' }}
    />
  );
}
