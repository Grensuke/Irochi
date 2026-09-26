# Frontend Context — Vibhinetra

> **This file describes the CURRENT state of the frontend.**
> It is NOT a conversation transcript. Update it after each approved checkpoint.

---

## Phase

E2E Real PCAP Validation Complete. (Integration verified with actual telemetry.)

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
- TypeScript check passes (0 errors)
- Production build succeeds
- Alerts and Live WebSocket integrated with REAL backend pipeline
- Meniscus liquid-socket navigation dock component (`MeniscusNavbar`) implemented for public and app navigation
- Simplex Data-Diode Flow Dynamics visualizer (`DiodeFlowVisualizer`) implemented and integrated into Network page
- Visual Polish Phase: Updated `ThreatTimeline`, `SeverityDistribution`, `TopSources`, `TopTargets`, and `SummaryBar` with SOC-grade aesthetics and data-sync capabilities.
- Added `NarrativePanel` and AI progression/correlation utilities (`correlation.ts`, `explanation.ts`, `progression.ts`, `recommendations.ts`).
- Added `AlertDetailPage` featuring `IncidentPanel`, `EvidenceChain` (Kill-Chain Progression), and Timeline Playback controls, natively styled using standard CSS framework (removed Tailwind dependencies).
- Added `useIncidents` and `useIncident` hooks for fetching Incident entities from the new backend REST API endpoints.
- Updated `Threats` page to map the new `unknown_threat` (now displayed as `Unknown Threat`) and `unknown_detector` metadata.
- Upgraded telemetry screens (`Network`, `Traffic`, `DiodeFlowVisualizer`, `SummaryBar`) from idle mock states to active live-simulation modes with particle systems, mock event generators, and animated charts.
- Redesigned `Investigation.tsx` into an advanced Incident Investigation Queue UI with risk scores and visual phase indicators.
- Added "Export to PDF" capability using `jspdf` to `AlertDetailPage.tsx` integrating AI narrative data.
- Refined UI across alert tables and feeds to display structured severity tags (`SEVERITY: CRITICAL`).
- Implemented **silent background refetching** in `useDashboard` and `useAlerts` to allow real-time reactivity to backend updates without visual flashing or constant loading states.
- Removed SIH/SIH26145 branding references from UI labels and internal translation tokens.
- Restyled `MeniscusNavbar` to use a dynamic MacOS segmented-control aesthetic and CSS Grid for perfect centering, decoupling it from hardcoded colors.
- Upgraded PDF Export Engine (`exportPdf.ts`): Refactored to a clean "white-label" theme, completely fixed Unicode rendering bugs (manual checkmarks), and implemented a robust dynamic line-wrapping and progressive text-scaling algorithm for KPI boxes to guarantee zero text overflow on long threat labels.
- Added a 7th capability ("Unknown/Anomaly Detector") to the Landing Page and configured its grid layout to be full-width centered.
- **End-to-End Validation**: Passed all visual and data-sync E2E validations using real PCAP data (Friday-WorkingHours). Incident queues, AI narratives, PDF exports, and telemetry views were verified via an automated UI subagent.

## Frontend Structure

```text
frontend/
├── public/
│   ├── vibhinetra-logo.jpg # Official Brand Logo Emblem
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── DiodeFlowVisualizer.tsx / DiodeFlowVisualizer.css   # Simplex Data-Diode flow dynamics visualizer
│   │   ├── VibhinetraLogo.tsx / VibhinetraLogo.css                     # Brand logo & cyber shield emblem
│   │   ├── VerticalMeniscusRail.tsx / VerticalMeniscusRail.css # Collapsed sidebar liquid rail
│   │   ├── MeniscusNavbar.tsx / MeniscusNavbar.css             # Fluid liquid dock navigation
│   │   ├── Header.tsx / Header.css
│   │   ├── SummaryBar.tsx / SummaryBar.css
│   │   ├── ThreatBreakdown.tsx / ThreatBreakdown.css
│   │   ├── UnidirectionalThreatStream.tsx / UnidirectionalThreatStream.css # Animated data stream overlay
│   │   ├── AlertTable.tsx / AlertTable.css
│   │   ├── AlertDetail.tsx / AlertDetail.css
│   │   └── LiveFeed.tsx / LiveFeed.css
│   ├── contexts/
│   │   └── AuthContext.tsx # Mock auth
│   ├── hooks/
│   │   ├── useDashboard.ts
│   │   ├── useAlerts.ts
│   │   ├── useLiveAlerts.ts
│   │   ├── useIncidents.ts
│   │   ├── useIncident.ts
│   │   └── useLiveTelemetry.ts
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

## Integration Status: Real vs Mock

**REAL (Integrated with PostgreSQL / Redis via Backend):**
| Endpoint | Used By |
|---|---|
| GET /api/v1/health | `api.ts` (available, not displayed in UI) |
| GET /api/v1/alerts | `useAlerts` → AlertTable, Alerts page |
| GET /api/v1/incidents | `useIncidents` → Overview, Investigation page |
| GET /api/v1/incidents/{id} | `useIncident` → AlertDetailPage |
| GET /api/v1/dashboard/summary | `useDashboard` → SummaryBar, ThreatBreakdown, Threats page, Analytics page |
| WS /api/v1/ws/alerts | `useLiveAlerts` → LiveFeed |
| WS /api/v1/ws/telemetry | `useLiveTelemetry` → Network, SummaryBar |

**MOCK / DEMO (Simulated Data):**
- Analytics trends (synthetic historical charts)
- Traffic charts (synthetic throughput/protocol data)
- Settings (UI only)

## Pending

- Implement historical analytics APIs to replace mock Analytics trends
- Real authentication and authorization
- Real multi-tenancy support

## Known Constraints

- Telemetry screens (Network/Analytics) are still mock demos.
- CORS is permissive ("*") on backend — suitable for dev only.
- Vite dev proxy handles API routing — production will need nginx/reverse proxy.
- No real authentication (auth context is mock only).
