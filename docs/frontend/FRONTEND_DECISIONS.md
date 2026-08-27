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
