import { useState, useEffect } from 'react';

export function useLiveTelemetry() {
  const [flows, setFlows] = useState(0);
  const [throughput, setThroughput] = useState(0);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let isCleanedUp = false;

    const connect = () => {
      if (isCleanedUp) return;
      
      const defaultWsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
    const wsUrl = `${import.meta.env.VITE_WS_URL || defaultWsUrl}/api/v1/ws/telemetry`;
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.bytes_per_sec !== undefined) {
            setFlows(data.flows_per_sec || 0);
            setThroughput((data.bytes_per_sec * 8) / 1000000);

            if (data.events && Array.isArray(data.events) && data.events.length > 0) {
              const mapped = data.events.map((raw: any) => ({
                id: raw.event_id || `evt_${Date.now()}_${Math.random()}`,
                type: raw.event_type,
                time: raw.timestamp ? new Date(raw.timestamp / 1000).toISOString() : new Date().toISOString(),
                connection: `${raw.src_ip}:${raw.src_port || '*'} ➔ ${raw.dst_ip}:${raw.dst_port || '*'}`,
                source: raw.src_ip,
                destination: raw.dst_ip,
                protocol: raw.protocol,
                sent: raw.payload?.orig_bytes || 0,
                received: raw.payload?.resp_bytes || 0,
                state: raw.payload?.conn_state || '-',
                sensor: raw.sensor_source || 'vibhinetra-tap'
              }));
              
              setEvents(prev => {
                const next = [...mapped.reverse(), ...prev];
                return next.slice(0, 50);
              });
            }
          }
        } catch (e) {
          // ignore parsing errors
        }
      };

      ws.onclose = () => {
        if (isCleanedUp) return;
        setFlows(0);
        setThroughput(0);
        timer = setTimeout(connect, 2000);
      };
      
      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      isCleanedUp = true;
      if (timer) clearTimeout(timer);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, []);

  return { flows, throughput, events };
}
