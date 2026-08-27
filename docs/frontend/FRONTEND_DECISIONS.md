# Frontend Decisions — Irochi

> **This file records stable frontend-area decisions.**
> It is NOT a chat history. Add entries when decisions are made.

---

## FD-001: React + Vite + TypeScript

**Status:** Locked

The frontend uses React + Vite + TypeScript. Do not replace this stack without explicit project-lead approval.

## FD-002: FastAPI as Backend Boundary

**Status:** Locked

The frontend communicates exclusively through FastAPI. React never connects directly to PostgreSQL, Redis, or Redpanda.

## FD-003: REST + WebSocket Integration

**Status:** Locked

REST endpoints for data queries and CRUD operations. WebSocket for live alert delivery. These are the intended integration mechanisms between frontend and backend.

## FD-004: Browser Never Accesses Infrastructure Services

**Status:** Locked

The browser must not directly access PostgreSQL, Redis, Redpanda, or any other infrastructure service. All data flows through FastAPI.

## FD-005: Frontend Initially Uses Mock Services/Data

**Status:** Active

During the dummy/scaffold phase, the frontend uses mock services and data. A service layer (`frontend/src/services/`) will be used so mock services can later be replaced with real FastAPI calls.

## FD-006: Service Layer Architecture

**Status:** Active

All backend communication is routed through `frontend/src/services/`. Components never call `fetch()` or `WebSocket` directly. This enables:

- `api.ts` — REST API client (fetch wrapper with proxy routing)
- `websocket.ts` — WebSocket client (connection state + protocol handling)

Future real implementations swap these service files without changing hooks or components.

## FD-007: Design System — Dark SOC Operations Theme

**Status:** Active

Design direction: professional SOC/cybersecurity analyst dashboard.

- **Typography:** Inter (UI text) + Fira Code (technical values: IPs, alert IDs, hashes, timestamps)
- **Color palette:** Dark ops (#0a0e14 base), high-contrast severity colors (red/orange/yellow/teal/gray)
- **Monospace for technical data:** All IPs, ports, alert IDs, and technical identifiers use `font-mono`
- **Severity hierarchy:** Visual priority critical → high → medium → low → info with distinct color-coded badges
- **Phase distinction:** Backfilled alerts (purple badge) vs live alerts (green pulsing badge)

This is NOT the final production design. It establishes the baseline aesthetic direction for future iteration.

## FD-008: Frontend Domain Types Separate from Canonical Schema

**Status:** Active

Frontend types in `src/types/index.ts` are PRESENTATION types matching the API response structure. They are NOT the Canonical Event Schema. Alert presentation fields and canonical network telemetry concepts are kept separate per the architecture checkpoint.

## FD-009: Product Shell Architecture & Routing

**Status:** Active

- **Router:** React Router v7 is used for client-side routing.
- **Auth Context:** A mock authentication context separates public routes (Landing, Login) from protected routes (App Shell).
- **Layout:** Authenticated pages are wrapped in `AppLayout` providing the sidebar navigation and top header.
- **Status Semantics:** Alert statuses use analyst workflow terminology (`new`, `investigating`, `closed`, `false_positive`), strictly avoiding "resolved" to reinforce Irochi's passive nature.
