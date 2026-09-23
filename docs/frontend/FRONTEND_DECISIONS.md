# Frontend Decisions — Vibhinetra

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

**Status:** Obsolete (For Core Data) / Active (For Auth/Telemetry)

During the initial dummy/scaffold phase, the frontend used mock services and data. The frontend has now been updated to consume the real FastAPI REST and WebSocket endpoints for Alerts and Incidents. However, Authentication and certain Telemetry visualizations (Network, Analytics) still rely on mock data and contexts until their backend counterparts are finalized.

## FD-006: Service Layer Architecture

**Status:** Active

All backend communication is routed through `frontend/src/services/`. Components never call `fetch()` or `WebSocket` directly. This enables:

- `api.ts` — REST API client (fetch wrapper with proxy routing)
- `websocket.ts` — WebSocket client (connection state + protocol handling)
- `mockData.ts` — Mock services for incomplete backend features (e.g., telemetry)

This allowed the seamless swap from initial mock implementations to the current real FastAPI integration for core alerts without changing hooks or components.

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
- **Status Semantics:** Alert statuses use analyst workflow terminology (`new`, `investigating`, `closed`, `false_positive`), strictly avoiding "resolved" to reinforce Vibhinetra's passive nature.

## FD-010: Floating Pill Navigation Dock & Collapsed Rail Component

**Status:** Active

High-fidelity floating indicator navigation components (`VerticalMeniscusRail` and `MeniscusNavbar`):
- **Horizontal Floating Pill Dock:** Frosted glass capsule container with a hardware-accelerated floating pill indicator that glides fluidly across tabs using cubic-bezier spring physics (`cubic-bezier(0.16, 1, 0.3, 1)`).
- **Collapsed Sidebar Floating Bubble Rail:** Vertical navigation rail with a floating bubble indicator smoothly highlighting the active SOC module with popout hover tooltips.
- **Theme-Adaptive Palette (Dark & Light Modes):**
  - **Dark Mode:** Dark frosted glass container (`rgba(22, 25, 34, 0.85)`), metallic gradient pill (`linear-gradient(180deg, #2e3544, #1e232e)`), muted slate text (`#94a3b8`), and crisp white active indicators (`#ffffff`).
  - **Light Mode:** Frosted white glass container (`rgba(255, 255, 255, 0.95)`), dark charcoal pill (`#0f172a`), slate text (`#64748b`), and crisp white active items (`#ffffff`).
- **Smooth 120 FPS Transitions:** Hardware-accelerated GPU transitions with zero edge artifacts, zero harsh popups, and smooth color crossfading.
- **Unified Navigation:** Full React Router integration and keyboard accessibility without any separate bottom floating dock.

## FD-011: Client-Side PDF Generation

**Status:** Locked

Report generation (PDF) is performed entirely client-side using `jspdf` and canvas drawing methods. This avoids introducing heavy backend dependencies (e.g., WeasyPrint, wkhtmltopdf) and keeps the FastAPI backend purely focused on intelligence data delivery.

## FD-012: Live Telemetry Simulation in UI

**Status:** Active

Prior to physical integration, telemetry visualizers (`DiodeFlowVisualizer`, `UnidirectionalThreatStream`, `Traffic`, `SummaryBar`) are implemented using live-simulated active states (e.g., particle systems, animated SVG graphs, simulated flow rates) rather than idle empty states. This ensures the SOC dashboard feels active and facilitates UX testing of data-dense environments.

## FD-013: Silent Background Refetching for UI Reactivity

**Status:** Locked

Dashboard components relying on rapid state changes (like metric bars and dynamic telemetry) must employ silent background refetching (e.g., bypassing global loading indicators during polling) to ensure visual continuity. Using standard polling that triggers full-component loading flashes or resets the UI is strictly prohibited in real-time operational views.
