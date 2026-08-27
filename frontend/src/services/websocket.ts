/**
 * WebSocket service — live alert connection to the dummy backend.
 *
 * Implements the dummy WS protocol:
 *   1. Connect → receive backfill alerts
 *   2. Receive backfill_complete marker
 *   3. Receive live alerts periodically
 *
 * Manages connection state and automatic reconnection.
 */

import type { Alert, ConnectionState, WsMessage } from '../types';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/alerts`;

const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

export type AlertHandler = (alert: Alert, phase: 'backfill' | 'live') => void;
export type StateHandler = (state: ConnectionState) => void;

export class AlertWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  private onAlert: AlertHandler;
  private onStateChange: StateHandler;
  private onBackfillComplete: (() => void) | null;

  constructor(
    onAlert: AlertHandler,
    onStateChange: StateHandler,
    onBackfillComplete?: () => void,
  ) {
    this.onAlert = onAlert;
    this.onStateChange = onStateChange;
    this.onBackfillComplete = onBackfillComplete ?? null;
  }

  connect(): void {
    if (this.destroyed) return;
    this.cleanup();

    this.onStateChange('connecting');
    this.ws = new WebSocket(WS_URL);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.onStateChange('backfilling');
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);

        if (msg.type === 'backfill' && msg.alert) {
          this.onAlert(msg.alert, 'backfill');
        } else if (msg.type === 'backfill_complete') {
          this.onStateChange('live');
          this.onBackfillComplete?.();
        } else if (msg.type === 'live' && msg.alert) {
          this.onAlert(msg.alert, 'live');
        }
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      if (this.destroyed) return;
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  disconnect(): void {
    this.destroyed = true;
    this.cleanup();
    this.onStateChange('disconnected');
  }

  private cleanup(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close();
      }
      this.ws = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      this.onStateChange('disconnected');
      return;
    }
    this.onStateChange('reconnecting');
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, RECONNECT_DELAY_MS);
  }
}
