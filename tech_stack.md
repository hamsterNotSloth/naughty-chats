# Technical Stack & Architecture Overview

Version: 0.1 Draft  
Last Updated: 2025-09-13  
Owner: Engineering  
Related Docs: `PRD.md`, `screens.md`

---
## 1. Purpose

This document centralizes the implementation-focused technology decisions for Naughty Chats. While the PRD captures *what* we will build, this file captures *how* we intend to build, operate, scale, and evolve it. It is designed for engineers, SRE, DevOps, data, and security reviewers. Changes here should remain living and versioned via PR.

---
## 2. High-Level Architecture Summary

User (Browser) → Next.js (SSR + Client) → FastAPI Backend (REST + WebSocket) → Services Layer (Auth, Characters, Chat, Image Jobs, Economy) → Async Workers / Model Inference Providers (RunPod) → Data Stores (Postgres, Redis, Blob Storage) → Observability & Payments (Stripe or Alt Provider).

Edge & Delivery: CDN / Front Door terminates TLS and routes to frontend (Next.js) and API (Container Apps). WebSockets proxied through same API origin for simplicity.

---
|---------|--------|-----------|----------------|
| Language | TypeScript | Type safety + tooling | Strict mode enabled |
| UI Styling | Tailwind CSS v4 | Rapid iteration, design tokens later | Consider extracting component library in Phase 2 |
| Headless Components | Headless UI + minimal custom | Accessibility baseline | Radix optional if complex popovers needed |
| State (Server) | React Query (TanStack) | Caching, mutation ergonomics | Central query keys documented below |
| State (UI/Ephemeral) | Zustand (light slices) | Avoid Redux overhead | Keep slices small (<300 LOC rule) |
| Auth Handling | Bearer token stored (memory) + refresh cookie (future) | Security vs XSS risk | Implement refresh rotation Phase 1.1 |
| Forms / Validation | Zod (planned) or native + HTML constraints | Type-safe schemas | Add when forms expand (character wizard) |
| Analytics | Lightweight custom event dispatcher → backend ingest | Control & cost | Later segment-like integration optional |
| Image Display | Next/Image | CDN + optimization | Ensure proper cache headers |
| Internationalization | N/A (MVP) | Scope reduction | Plan for next-i18n if needed |

### 3.1 React Query Key Conventions (Proposed)

- `characters:list:{filtersHash}`
- `character:detail:{id}`
- `chat:session:{sessionId}` (stream merges patches)
- `image:job:{jobId}`
- `gems:balance` / `gems:ledger:{page}`

### 3.2 Performance

- Use `suspense` where beneficial for initial character list.
---

| Concern | Choice | Rationale | Notes / Future |
|---------|--------|-----------|----------------|
| Framework | FastAPI | Async IO + type hints + speed | Mature ecosystem |
| ASGI Server | Uvicorn (workers=auto) | Simplicity | Consider gunicorn supervisor if needed |
| Auth | JWT (HS256) short-lived access | Simplicity MVP | Migrate to RS256 + refresh rotation + Key rotation (Key Vault) |
| Password Hash | passlib (bcrypt) | Security standard | Adjust cost factor with perf tests |
| Input Validation | Pydantic v2 | Built-in with FastAPI | Add custom validators for moderation tags |
| Config | python-dotenv → env vars | Simplicity local | Move secrets to Key Vault binding |
| Rate Limiting | (Planned) Redis counters | Abuse prevention | Library: slowapi or custom middleware |
| Background Tasks | Separate worker (Celery or custom asyncio) | Async job handling | Decide early; Celery if scheduling needed |
| Messaging | Redis Streams or Azure Service Bus | Queued events | Start with Redis; migrate when scale demands |
| Image Job Polling | Scheduled worker pull from RunPod | Simplicity first | Event push if provider adds webhook |
| Moderation | Pre/post filters + async review queue | Risk mitigation | Use provider classifiers + custom rules |

### 4.1 Service Layer Modules (Proposed)

- `auth_service.py`
- `character_service.py`
- `chat_service.py`
- `image_service.py`
- `economy_service.py`
- `affiliate_service.py`
- `moderation_service.py`
- `analytics_service.py`
Each module exposes pure functions or small classes; avoid deep inheritance. Dependency injection via FastAPI `Depends` or explicit parameters.

### 4.2 API Style

- Brute force lockouts (username/email + IP) with exponential backoff.
- Switch to RS256 JWT with rotated keys in Key Vault; kid header referencing key version.
- Add CSRF protection for refresh token flow.

---
## 5. Data & Storage

| Type | Technology | Purpose | Notes |
|------|------------|---------|-------|
| Primary DB | PostgreSQL (Flexible Server) | Core relational entities | Schema versioning via Alembic |
| Cache / Rate Limit | Redis | Low latency access, counters | TTL strategy doc to follow |
| Search (Phase 2+) | (Temp) Postgres full text → Azure AI Search later | Character/tag search | Abstraction boundary early |
| Queue / Events | Redis Streams (MVP) → Service Bus | Job + moderation events | Migration strategy doc later |
| Analytics (Later) | Event table + export pipeline | KPI instrumentation | Offload to warehouse when volume grows |

### 5.1 Schema Principles

- Immutable ledger lines; derive balance server-side.
- Soft deletes with `deleted_at` for reversible moderation actions.
- Audit columns: `created_at`, `updated_at`, `created_by` where relevant.

---
## 6. AI / ML Model Layer

| Function | Provider | Model Class | Notes |
|----------|----------|------------|-------|
| Chat LLM | RunPod hosted LLM (7B–13B instruct tuned) | Transformer | Optimized for latency vs cost; streaming tokens |
| Image Gen | RunPod diffusion (e.g., SDXL variant) | Diffusion | QoS tiers map to steps / CFG / resolution |
| Moderation Text | Open-source classifier + heuristic layer | Multi-label | Ensemble later for recall; evaluate Azure Content Safety later |
| Moderation Image | Open-source NSFW / policy model (RunPod worker) | CNN / ViT | Async retroactive removal; threshold tuning required |
| Suggested Prompts (P2) | Same Chat LLM instance | Transformer | Prompt templating; cached per character 10m |

### 6.1 Abstraction Interface (Example)

```python
class ModelService:
    def generate_chat_reply(self, session_id: str, prompt: str, persona: dict) -> AsyncIterator[str]: ...
    def submit_image_job(self, params: ImageJobParams) -> JobId: ...
    def fetch_image_job(self, job_id: str) -> ImageJobStatus: ...

### 6.2 RunPod Justification & Governance

RunPod is selected as the unified AI inference platform (chat + image) for MVP due to:

| Dimension | RunPod Advantage | Impact |
|----------|------------------|--------|
| Cost / Flexibility | Pay-per-minute GPU with rapid scale, choice of community & custom models | Lowers initial burn, faster experimentation |
| Model Freedom (NSFW) | Fewer policy constraints for adult roleplay models vs some managed platforms | Enables core differentiating content safely within internal policy controls |
| Latency Control | Ability to pin dedicated GPU pods and warm them | Predictable first-token latency targets |
| Customization | Easy swap / fine-tune / weights update without provider approval cycles | Accelerates iteration loops |
| Multi-Modal Cohesion | Co-locate LLM + diffusion workers to reduce cross-provider variance | Simplifies metrics + cost accounting |

Mitigations & Controls:
- Content Safety Layer: Text + image moderation applied pre & post (open-source classifiers + rules) to compensate for lack of provider-enforced policy.
- Isolation: Dedicated pods; no multi-tenant inference for sensitive traffic.
- Observability: Structured per-request tracing (model_id, tokens, latency, cost_estimate).
- Fallback Strategy: Maintain abstraction to later plug Azure-hosted or alternative provider endpoints if compliance landscape changes.
- License Compliance: Maintain curated allow-list of model versions & licenses (stored in DB table `model_registry`).

### 6.3 Cost Control

- Track `cost_per_token`, `tokens_per_second`, and `gpu_minute_cost` → weekly margin review vs gem pricing.
- Dynamic quality tiers: Balanced vs Premium (differs in diffusion steps / cfg scale / resolution; LLM maybe changes temperature + top_p only).
- Auto scale-down: Terminate idle diffusion pods after configurable idle window (e.g., 5m) while keeping a minimal warm chat pod.
- Adaptive Context Truncation: Trim conversation history by token budget heuristic before inference to cap token cost.
- Batch Image Scheduling: Group small image jobs if queue depth > threshold to maximize GPU utilization.

### 6.4 Risk Matrix (RunPod Specific)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Model supply drift (quality degradation) | Med | Med | Version pinning; regression benchmarks on persona test set |
| Cost spike (GPU market fluctuation) | Med | High | Budget alerts; automated switch to cheaper tier or reduced quality preset |
| Policy / compliance scrutiny | Med | High | Internal audit logs; documented taxonomy filters; rapid disable switch per model |
| Latency variance under burst | High | Med | Pre-warmed standby pods; queue smoothing + backpressure banner |
| Jailbreak prompts bypass filters | High | Med | Layered output classifier + pattern redaction + user report pipeline |

### 6.5 Future Azure Alignment (Optional Roadmap)
- Evaluate Azure AI Content Safety integration for a second-layer moderation.
- Pilot Azure model endpoints for baseline SFW persona variant to compare retention & cost.
- If enterprise clients request stricter compliance, introduce dual-path: Azure (strict) vs RunPod (creative) selectable per chat.
---
## 7. Payments & Economy

| Aspect | Decision | Notes |
|--------|----------|-------|
| Primary Provider | Stripe (MVP assumption) | Reliable, fast integration |
| Alt Providers | zkp2p / phyziro (Research) | Lower fees / global; abstracted |
| Integration Pattern | Server-created checkout session → webhook → ledger write (idempotent) | Prevent duplicate gem credits |
| Currency Packs | Config table (pack_id, gems, price, active) | Admin toggle future |
| Ledger | Append-only, foreign key to action (chat_msg_id, image_job_id, purchase_id) | Balance derived via SUM |
| Refund Policy | Failures auto-refund; manual adjustments via admin ledger entries | Document reasons enum |

---
## 8. Observability & Operations
| Concern | Tool | Notes |
|---------|------|-------|
| Logging | Structured JSON → Azure Log Analytics | Include correlation/request IDs |
| Metrics | Prometheus scrape → Azure Monitor | Export custom counters (latency, queue_depth) |
| Tracing | OpenTelemetry SDK | 100% sample in dev, downsample prod |
| Dashboards | Azure Portal + Grafana (optional) | SLO burn, latency, gem revenue |
| Alerting | Azure Monitor Alerts | p95 latency, error rate, queue backlog |

Runbook index (to create): auth failures spike, queue backlog growth, payment webhook retries.

---
## 9. Security & Compliance
- Secrets: Azure Key Vault; local `.env` only for dev.
- Principle of least privilege (separate managed identities per service).
- Content Moderation: layered text pre-filter + output scan; image scan async.
- Dependency Scanning: GitHub Dependabot + weekly `pip-audit` & `npm audit` review.
- Rate Limiting: IP + user dimension; exponential penalty windows.

---
## 10. Performance & Scaling
| Layer | Strategy |
|-------|----------|
| API | Horizontal scale on CPU + concurrency; async non-blocking model calls |
| Chat Streaming | Backpressure: send tokens in batches every ~50ms; client smooth render |
| Image Jobs | Queue; worker concurrency tuned to GPU availability |
| Caching | Character lists, pricing config, model metadata |
| DB | Proper indices on FK & frequent filters; connection pooling (pgbouncer later) |

---
## 11. Local Development Workflow
| Step | Tooling |
|------|---------|
| Python Env | `venv` + `pip install -r requirements.txt` |
| Frontend | `npm install` then `npm run dev` (Next.js) |
| Backend Run | `uvicorn main:app --reload` |
| Linting (Planned) | Ruff (Python), ESLint (JS/TS) |
| Type Checking | mypy (planned), `tsc --noEmit` |
| Tests (Planned) | pytest, React Testing Library |
| Env Vars | `.env.example` to be created |

Dev convenience: Add Makefile or Taskfile for common commands.

---
## 12. Risks / Open Decisions (Engineering)
| Topic | Status | Notes |
|-------|--------|-------|
| Celery vs custom workers | TBD | Decide before implementing image queue |
| Redis vs Service Bus | Start Redis | Migrate when scaling beyond single region |
| RS256 JWT & rotation | Phase 1.1 | Needs Key Vault integration |
| Alt payments adoption | Research | Evaluate legal/compliance risk |
| Search provider | Defer | Postgres FTS adequate early |
| WebSocket scaling | Prototype | Consider separate service if connection load high |

---
## 13. Change Management
All modifications via PR referencing issue. Include section diff in PR description. Maintain semantic commit tags (`infra:`, `feat:`, `chore:`, `sec:` etc.).

---
## 14. Appendix
### 14.1 Proposed Directory Additions
```
backend/
  services/
  models/  # SQLAlchemy or Pydantic models
  workers/
  routers/
infra/
  bicep/ (future)
frontend/
  src/
    lib/
    hooks/
    state/
```

### 14.2 Gem Pricing Config (Example Placeholder)
| Tier | Balanced | Premium |
|------|----------|---------|
| Chat (per AI msg) | 5 gems | 9 gems |
| Image (1x) | 20 gems | 45 gems |
| Image (4x batch) | 70 gems | 150 gems |

Adjust based on actual model cost analysis.

---
## 15. Summary
This stack emphasizes pragmatic, modular choices enabling fast iteration while keeping clear upgrade paths (keys rotation, queue migration, multi-model abstraction). As complexity grows, revisit: search service, dedicated feature flag service, structured event warehouse, and global edge inference.

> Next Actions: Implement service module scaffolding, decide worker framework, add infra as code baseline, and integrate Stripe sandbox.
