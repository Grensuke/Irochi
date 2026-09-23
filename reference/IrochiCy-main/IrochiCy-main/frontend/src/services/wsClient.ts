/* ═══════════════════════════════════════════════════════════════
   SIH-26145 WebSocket Client
   Singleton WS with reconnect, message parsing, and lifecycle
   ═══════════════════════════════════════════════════════════════ */

import type { WebSocketMessage, WebSocketStatus } from '@/types';

type MessageHandler = (msg: WebSocketMessage) => void;
type StatusHandler = (status: WebSocketStatus) => void;

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/alerts';

class WsClient {
  private static instance: WsClient | null = null;
  private ws: WebSocket | null = null;
  private messageHandlers = new Set<MessageHandler>();
  private statusHandlers = new Set<StatusHandler>();
  private status: WebSocketStatus = 'connecting';
  private reconnectAttempts = 0;
  private maxReconnectDelay = 30000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  static getInstance(): WsClient {
    if (!WsClient.instance) WsClient.instance = new WsClient();
    return WsClient.instance;
  }

  connect(token?: string) {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    
    try {
      const url = token ? `${WS_URL}?token=${token}` : WS_URL;
      this.ws = new WebSocket(url);
      this.setStatus('connecting');

      this.ws.onopen = () => {
        this.setStatus('live');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WebSocketMessage;
          this.messageHandlers.forEach(h => h(msg));
        } catch { /* ignore parse errors */ }
      };

      this.ws.onclose = () => {
        this.setStatus('reconnecting');
        this.scheduleReconnect(token);
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      this.setStatus('offline');
      this.scheduleReconnect(token);
    }
  }

  private scheduleReconnect(token?: string) {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.maxReconnectDelay);
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => this.connect(token), delay);
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this.setStatus('offline');
  }

  onMessage(handler: MessageHandler) { this.messageHandlers.add(handler); return () => { this.messageHandlers.delete(handler); }; }
  onStatus(handler: StatusHandler) { this.statusHandlers.add(handler); handler(this.status); return () => { this.statusHandlers.delete(handler); }; }

  getStatus() { return this.status; }
  getReconnectAttempts() { return this.reconnectAttempts; }

  private setStatus(s: WebSocketStatus) {
    this.status = s;
    this.statusHandlers.forEach(h => h(s));
  }
}

export const wsClient = WsClient.getInstance();
export default wsClient;
