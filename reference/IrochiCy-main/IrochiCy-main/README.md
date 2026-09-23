# SIH-26145 — Passive Network Threat Detection Platform

A professional SOC (Security Operations Center) analyst dashboard for real-time
network threat detection and security intelligence.

## Quick Start

```bash
# Install dependencies
npm install --ignore-scripts
npm install esbuild

# Development (mock mode)
npm run dev

# Production build
npm run build
```

## Credentials

| Username  | Password     | Role    |
|-----------|-------------|---------|
| analyst   | analyst123  | ANALYST |
| admin     | admin123    | ADMIN   |

## Environment Variables

| Variable           | Default                     | Description                         |
|--------------------|-----------------------------|-------------------------------------|
| VITE_MOCK          | `true`                      | Use mock data (`true`) or real API  |
| VITE_API_BASE_URL  | `/api/v1`                   | Backend REST base URL               |
| VITE_WS_URL        | `ws://localhost:8000/ws/alerts` | WebSocket URL for live alerts    |

### Mock Mode (default)

All data is generated client-side with realistic distributions. No backend
required. Auto-refresh and live streams use timers to simulate real-time data.

### Real API Mode

Set `VITE_MOCK=false` and configure `VITE_API_BASE_URL` and `VITE_WS_URL`:

```bash
VITE_MOCK=false VITE_API_BASE_URL=http://localhost:8000/api/v1 npm run dev
```

The API client (`src/services/api.ts`) handles:
- Bearer JWT authentication
- Auto-retry on 429 with exponential backoff
- Automatic redirect to /login on 401
- Typed response parsing

## Architecture

```
src/
├── components/          # Reusable UI components
│   ├── AlertOverviewCard/
│   ├── AlertTable/      # Filters, Table, Row, BulkActions, Pagination
│   ├── AdminSystem/     # System health dashboard
│   ├── AdminUsers/      # User management table
│   ├── AnalystNotes/
│   ├── AppShell/        # Sidebar + Header + Layout
│   ├── ConfidenceBar/
│   ├── ConfidenceHistogram/  # SVG confidence distribution
│   ├── ConnStateGrid/
│   ├── ConnectionLostBanner/
│   ├── ContextMenu/
│   ├── ErrorBanner/
│   ├── EvidenceTimeline/
│   ├── FlowVisualizer/  # Canvas-based flow animation
│   ├── InviteUserModal/
│   ├── KeyboardShortcuts/
│   ├── LiveFlowTable/
│   ├── Modal/
│   ├── PageTransition/
│   ├── ProfileSection/
│   ├── RawEventViewer/  # Syntax-highlighted JSON
│   ├── RelatedAlerts/
│   ├── SettingsSidebar/
│   ├── SeverityBadge/
│   ├── SignalBreakdown/
│   ├── Skeleton/        # Shimmer loading states
│   ├── StatusBadge/
│   ├── ThreatDetail/
│   ├── ThreatSelector/
│   ├── ThreatTypePill/
│   ├── Toast/           # Notification system
│   ├── ToggleSwitch/
│   ├── Tooltip/
│   └── TriagePanel/
├── context/
│   ├── AuthContext.tsx
│   ├── ThemeContext.tsx
│   └── UserPreferencesContext.tsx
├── hooks/
│   ├── useApiError.ts
│   ├── useKeyboardShortcuts.ts
│   ├── useTheme.ts
│   └── useWebSocket.ts
├── mocks/
│   └── mockService.ts   # 400+ lines of realistic data generators
├── pages/
│   ├── AlertDetailPage/ # Two-column triage workflow
│   ├── AlertsPage/      # Dense data table with filters
│   ├── DashboardPage/   # KPI strip + charts
│   ├── LoginPage/
│   ├── NetworkPage/     # Canvas viz + flow table
│   ├── NotFoundPage/    # Standalone 404
│   ├── SettingsPage/    # Profile, Appearance, Admin
│   └── ThreatsPage/     # Two-panel detector explorer
├── router/
│   ├── index.tsx        # Lazy-loaded routes with Suspense
│   └── RequireAuth.tsx
├── services/
│   ├── api.ts           # Typed fetch with retry
│   └── wsClient.ts      # Singleton WebSocket
├── styles/
│   ├── global.css
│   └── tokens.css       # CSS custom properties
└── types/
    └── index.ts         # All TypeScript interfaces
```

## Keyboard Shortcuts

| Keys  | Action           |
|-------|------------------|
| G + D | Go to Dashboard  |
| G + A | Go to Alerts     |
| G + N | Go to Network    |
| G + T | Go to Threats    |
| /     | Focus search bar |
| T     | Toggle theme     |
| Esc   | Close modal/menu |
| ?     | Show shortcuts   |

## Design System

- **Typography**: Inter (body), IBM Plex Mono (data/numbers)
- **Theme**: Dark-room precision with teal-cyan accent
- **Threat colors**: DDoS (#FF3B5C), Recon (#FF7A2F), DNS (#A78BFA), TLS (#5B8CFF), Exfil (#F5C518)
- **Accessibility**: prefers-reduced-motion, ARIA roles, keyboard navigation

## Stack

- React 18 + TypeScript (strict mode)
- Vite 6 with code splitting
- No UI library — all custom components
- CSS custom properties + plain CSS
- Canvas API for flow visualization
- SVG for charts and histograms
