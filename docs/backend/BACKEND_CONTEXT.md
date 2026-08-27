# Backend Context — Irochi

> **This file describes the CURRENT state of the backend.**
> It is NOT a conversation transcript. Update it after each approved checkpoint.

---

## Phase

Repository initialization / dummy backend

## Completed

- Repository and workflow structure setup
- Documentation structure created
- `.gitignore`, `AGENTS.md`, `README.md`, `.env.example`, `docker-compose.yml`
- Backend/frontend context and decision files
- Shared documents (API contract, data contracts, integration notes)

## Current Task

Dummy backend foundation (Checkpoint 2, pending approval)

## Pending

- FastAPI skeleton
- Dummy API endpoints
- Backend tests
- Redpanda topic design
- Feature/Window Schema
- Detector input/output contracts
- Alert Schema
- PostgreSQL schema
- Real Zeek integration
- Real ML models
- Production Redis (hot state + Pub/Sub)
- Real NetFlow/IPFIX adapter

## Known Constraints

- Real detection pipeline is not implemented
- Mock services are temporary placeholders
- Final API contract is not locked
- No real database, message broker, or ML in this phase

## Next Steps

Build the FastAPI dummy skeleton with mock endpoints per Checkpoint 2.
