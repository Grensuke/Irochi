# Frontend Context — Irochi

> **This file describes the CURRENT state of the frontend.**
> It is NOT a conversation transcript. Update it after each approved checkpoint.

---

## Phase

Checkpoint 4 (Dummy End-to-End Integration Validated)

## Completed

- Repository and workflow structure setup (Checkpoint 1)
- React + Vite + TypeScript project initialized (Checkpoint 3)
- SOC dashboard design system — dark ops palette, Inter + Fira Code typography (Checkpoint 3)
- Domain types matching backend API contract (presentation types, not Canonical Event Schema) (Checkpoint 3)
- Service layer: REST API client + WebSocket client + Mock Data Service (Checkpoint 3)
- React Router v7 setup with public/protected routes (Checkpoint 3)
- Mock Auth Context (Checkpoint 3)
- Pages: Landing, Login, Overview, Alerts, Threats, Network, Analytics, Settings, NotFound, AccessDenied (Checkpoint 3)
- Loading, empty, and error states for all data-consuming components (Checkpoint 3)
- WebSocket connection state display (connecting, backfilling, live, reconnecting, disconnected) (Checkpoint 3)
- Visible distinction between backfilled and live alerts (phase badges) (Checkpoint 3)
- Frontend Dockerfile (Checkpoint 3)
- TypeScript check passes (0 errors) (Checkpoint 3 & 4)
- Production build succeeds (Checkpoint 3 & 4)
- End-to-End dummy integration with FastAPI backend verified (Checkpoint 4)
- Meniscus liquid-socket navigation dock component (`MeniscusNavbar`) implemented for public and app navigation
- Simplex Data-Diode Flow Dynamics visualizer (`DiodeFlowVisualizer`) implemented and integrated into Network page

## Frontend Structure

```text
frontend/
├── public/
│   ├── irochi-logo.jpg # Official Brand Logo Emblem
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── DiodeFlowVisualizer.tsx / DiodeFlowVisualizer.css   # Simplex Data-Diode flow dynamics visualizer
│   │   ├── IrochiLogo.tsx / IrochiLogo.css                     # Brand logo & cyber shield emblem
│   │   ├── VerticalMeniscusRail.tsx / VerticalMeniscusRail.css # Collapsed sidebar liquid rail
│   │   ├── MeniscusNavbar.tsx / MeniscusNavbar.css             # Fluid liquid dock navigation
│   │   ├── Header.tsx / Header.css
│   │   ├── SummaryBar.tsx / SummaryBar.css
│   │   ├── ThreatBreakdown.tsx / ThreatBreakdown.css
│   │   ├── AlertTable.tsx / AlertTable.css
│   │   ├── AlertDetail.tsx / AlertDetail.css
│   │   └── LiveFeed.tsx / LiveFeed.css
│   ├── contexts/
│   │   └── AuthContext.tsx # Mock auth
│   ├── hooks/
│   │   ├── useDashboard.ts
│   │   ├── useAlerts.ts
│   │   └── useLiveAlerts.ts
│   ├── layouts/
│   │   └── AppLayout.tsx / AppLayout.css
│   ├── pages/
│   │   ├── Landing.tsx / Landing.css
│   │   ├── Login.tsx / Login.css
│   │   ├── Overview.tsx / Overview.css
│   │   ├── Alerts.tsx / Alerts.css
│   │   ├── Threats.tsx / Threats.css
│   │   ├── Network.tsx / Network.css
│   │   ├── Analytics.tsx / Analytics.css
│   │   ├── Settings.tsx / Settings.css
│   │   ├── NotFound.tsx
│   │   └── AccessDenied.tsx
│   ├── services/
│   │   ├── api.ts          # REST API client
│   │   ├── websocket.ts    # WebSocket client
│   │   └── mockData.ts     # Mock data for UI without API
│   ├── types/
│   │   └── index.ts        # Domain types
│   ├── utils/
│   │   └── format.ts       # Display helpers
│   ├── App.tsx             # App wrapper
│   ├── router.tsx          # React Router definition
│   ├── main.tsx
│   └── index.css           # Design system tokens
├── Dockerfile
├── index.html
├── package.json
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
└── vite.config.ts           # Proxy to backend
```

## API Endpoints Consumed

| Endpoint | Used By |
|---|---|
| GET /api/v1/health | api.ts (available, not displayed in UI) |
| GET /api/v1/alerts | useAlerts → AlertTable, Alerts page |
| GET /api/v1/dashboard/summary | useDashboard → SummaryBar, ThreatBreakdown, Threats page, Analytics page |
| WS /api/v1/ws/alerts | useLiveAlerts → LiveFeed |

*Other pages (Network, Analytics trends, Settings) use mock data from `src/services/mockData.ts`.*

## Pending

- Final API contract integration
- Real backend implementation for all mock data
- Real authentication and authorization
- Real multi-tenancy support

## Known Constraints

- Uses dummy backend endpoints and mock data.
- CORS is permissive ("*") on backend — suitable for dev only.
- Vite dev proxy handles API routing — production will need nginx/reverse proxy.
- No real authentication (auth context is mock only).
- No real-time data beyond dummy WS.

## Next Steps

Wait for project lead approval to proceed to production infrastructure and real architecture implementation.
