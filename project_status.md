# Project Status – Naughty Chats (As of 2025-09-15)

## 1. Executive Snapshot

Environment is partially infrastructure-as-code enabled. Core application (FastAPI backend + Next.js frontend) runs in Azure Container Apps with Cosmos DB and Entra ID–based auth (foundation for External ID / B2C). Local custom auth removed. Pending work centers on production‐grade identity (social providers), secret hardening, CI/CD automation, and observability.

| Dimension | Current | Target (Next 2 Sprints) | Notes |
|----------|---------|--------------------------|-------|
| Auth | Entra ID access tokens; B2C variables scaffolded | Full External ID (Google + Twitter + Discord) | Need B2C tenant config + provider wiring |
| API Images | Manually built & pushed; placeholder params in Bicep | Deterministic SHA tagging via azd pipeline | Add image tag parameters |
| Infra | Bicep `main.bicep` + `azure.yaml` scaffolded | Parameterized & repeatable `azd up` across envs | Need env value population |
| Data | Cosmos DB (users, characters) | Add RU optimization + indexing plan | Add composite indexes after telemetry |
| Secrets | Stored as Container App secrets (Cosmos key, ACR creds) | Managed Identity + Key Vault | Replace ACR creds with AcrPull MI role |
| Observability | Log Analytics only | App Insights + OTel traces + structured logs | Introduce correlation IDs |
| Testing | Unit tests for auth token validation (standard + B2C) | Broader API integration tests (CRUD, errors) | Add load test harness (Locust/JMeter) |
| CI/CD | Manual CLI + local docker builds | GitHub Actions w/ build scan deploy (azd) | Include security scanning (Trivy / CodeQL) |
| Docs | README + deployment.md v1 + B2C section | Hardened runbooks + ops playbook | Add incident & rollback guide |

## 2. Current Architecture Diagram (Conceptual)

SPA (Next.js) -> (Bearer token) -> FastAPI API -> Cosmos DB
        |                          ^
        v                          |
   Entra (B2C)  <------------------+

Logging: Container Apps -> Log Analytics

Images: GitHub local build -> ACR

## 3. Source of Truth Files

- Infrastructure: `infra/main.bicep`, `azure.yaml`
- Backend Auth Logic: `backend/entra_auth.py`
- Frontend MSAL Provider: `frontend/src/components/providers/AuthProvider.tsx`
- Test Coverage: `backend/tests/test_auth.py`
- Deployment Docs: `deployment.md`

## 4. Environment Strategy

| Env | Purpose | Status | Differences Needed |
|-----|---------|--------|--------------------|
| dev | Active development | Running | Lower RU (400), relaxed CORS, verbose logs |
| staging | Pre‑prod validation | Planned | Same infra + feature flags, synthetic data |
| prod | Customer traffic | Planned | Higher RU, strict CORS, Key Vault, scaling rules |

## 5. Identity & Auth Status

- Two app registrations required (API + SPA). Not yet fully parameterized (awaiting App IDs from tenant if not already extracted).
- B2C support code present; user flow/policy environment variables reserved.
- Social providers (Google/Twitter/Discord) not yet configured; frontend still shows provider buttons but they all must funnel through B2C hosted UI once enabled.
- Token validation: Audience + issuer enforced; JWKS cached.

### 5.1 Missing Inputs

| Variable | Needed For | Action |
|----------|------------|--------|
| API App Registration App ID | ENTRA_API_AUDIENCE | Create / capture GUID |
| SPA App Registration App ID | Frontend MSAL init | Create / capture GUID |
| B2C Tenant Primary Domain | B2C issuer derivation | Confirm or create External ID tenant |
| B2C Policy Name | Hosted user flow | Standard: B2C_1_SIGNUPSIGNIN |
| Social provider client IDs/secrets | Identity federation | Create in provider consoles |

## 6. Infrastructure as Code Status

- Bicep covers: Log Analytics, Container Apps Env, ACR, Cosmos DB (account + DB + 2 containers), API & Web Container Apps.
- Parameters include API scope/client variables and B2C fields.
- Image parameters currently generic; need tag control + optional repository override.
- Next improvement: Extract repeated resource naming to a module folder (shared naming logic / outputs) if scaling resource count.

## 7. Gaps & Technical Debt

| Area | Gap | Impact | Priority | Mitigation |
|------|-----|--------|----------|------------|
| Secrets | Using raw Cosmos key | Security / rotation friction | High | Add User‑Assigned MI + RBAC + Key Vault references |
| ACR Auth | Username/password in secrets | Secret sprawl | High | Assign AcrPull role to MI |
| Monitoring | No tracing / metrics segmentation | Slower incident triage | High | Add App Insights + OpenTelemetry |
| Logging | Unstructured prints (if any) | Hard to query | Medium | Integrate JSON logging w/ request IDs |
| CI/CD | Manual steps | Inconsistent deploys | High | GitHub Actions (lint/test/build/scan/azd deploy) |
| Frontend Auth UI | Custom email/password fields still visible | User confusion | Medium | Replace with redirect‐only flow |
| Error Handling | Generic 500 on empty character list | UX & observability | Low | Graceful empty state |
| Indexing | Default indexing policy | RU inefficiency at scale | Medium | Profile & add selective composite indexes |

## 8. Immediate Next Steps (Actionable)

1. Capture / confirm API & SPA App IDs; set `ENTRA_API_AUDIENCE`, `spaClientId`, `spaApiScope` envs.
2. Create B2C user flow + enable Google; add placeholders for Twitter/Discord.
3. Update frontend signup/signin pages: remove native credential form; invoke `loginRedirect`.
4. Run `azd env new dev` + set environment values; execute `azd up` to reconcile infra.
5. Build & push versioned images (git SHA); run `azd deploy` to update Container Apps.
6. Add health probes (readiness & liveness) to API Container App via Bicep (HTTP GET /healthz).
7. Implement JSON structured logger + correlation ID middleware.
8. Author GitHub Actions workflow: build, scan (Trivy), test, azd deploy (dev branch) + manual prod approval.
9. Introduce Key Vault + Managed Identity (modify Bicep; rotate out Cosmos key usage).
10. Add App Insights + OpenTelemetry instrumentation (FastAPI + Next.js custom server metrics proxy).

## 9. Extended Roadmap (Subsequent)

- Pagination & filtering for characters.
- Role-based scopes (e.g., `characters.write`).
- Rate limiting (per IP/user) using Azure API Management or self-managed Redis token bucket.
- Content moderation pipeline (Azure AI Content Safety) for generated messages.
- Background job runner (Azure Container Apps Job or Functions) for async tasks.
- Cost optimization: autoscale rules (RPS, CPU) & RU throughput autoscale in Cosmos.

## 10. Risk Register (Live)

| Risk | Probability | Severity | Owner | Mitigation State |
|------|-------------|----------|-------|------------------|
| Misconfigured B2C issuer leads to login failures | M | H | Auth Lead | Derive issuer from env + add integration test |
| Token audience mismatch after scope rename | L | M | Backend | Freeze scope name; add regression test |
| Secrets leaked in logs | M | H | DevOps | Structured logging + secret filters (pending) |
| Cosmos hot partition | L | M | Backend | Monitor RU + add synthetic load tests |
| Social provider ToS changes | L | M | Product | Track provider announcements |

## 11. Validation & Quality Gates Plan

| Gate | Current Tooling | Target | Notes |
|------|-----------------|--------|-------|
| Lint/Format | (JS/TS ESLint config present) | Enforce on PR | Add Python lint (ruff) |
| Unit Tests | Limited auth tests | 80% critical path coverage | Add character CRUD tests |
| Security Scan | None | Trivy image scan + dep audit | Integrate into CI |
| Infra Drift | Manual detect | `azd up` idempotence + tf-like diff | Add scheduled drift job |
| Performance | None | Locust baseline (p95 latency) | After probes & logging |

## 12. Required Decisions (Blocking) – Highlight

| Decision | Options | Recommendation | Owner |
|----------|---------|----------------|-------|
| Scope naming strategy | `access` vs granular | Start with `access`; later expand | Backend |
| Image tag policy | latest vs SHA | Git SHA + short tag + semver for prod | DevOps |
| Logging format | plain vs JSON | JSON (structured) | Backend |
| Secrets backend | Stay in ACA vs Key Vault | Key Vault + MI | DevOps |
| Social direct buttons | Native provider jump vs generic B2C screen | Generic B2C (simpler) | Product/Auth |

## 13. Operational Runbooks (Seed / Redeploy / Rollback)

### 13.1 Seed Characters (Dev/Staging)

1. Get Cosmos endpoint & key (until RBAC).
2. Export env vars (see section 13 in `deployment.md`).
3. Run `python -m backend.seed_characters`.
4. Confirm documents exist (portal or SDK script).

### 13.2 Hotfix Deployment

1. Branch from prod tag.
2. Patch & run tests.
3. Build images locally or rely on CI override.
4. `azd deploy --service api` (or web) after approval.

### 13.3 Rollback

1. Identify last known good image digest (ACR manifest).
2. Update environment variable (future param) or redeploy referencing prior tag.
3. Validate `/healthz` & basic user flow.
4. Tag rollback commit for traceability.

## 14. Metrics & KPIs (Planned)

| KPI | Definition | Initial Target |
|-----|------------|----------------|
| Auth Success Rate | Successful logins / attempts | > 99% |
| p95 API Latency | Time for /api/characters | < 250ms dev, < 150ms prod |
| Error Rate | 5xx per minute | < 1% of requests |
| RU Efficiency | RU per character list | Optimize after baseline |
| Deployment MTTR | Time to restore after failed deploy | < 30 min |

## 15. Suggested Folder Additions (Planned)

| Folder | Purpose |
|--------|---------|
| `.github/workflows` | CI/CD pipelines |
| `ops/` | Runbooks, diagrams, incident templates |
| `load/` | Locust scripts & config |
| `telemetry/` | OpenTelemetry config & sampling policies |

## 16. Acceptance Criteria for "Phase 2 Complete"

- azd provisioning fully idempotent in dev + staging.
- MSAL B2C login (email + Google) working end‑to‑end with protected API call.
- GitHub Actions pipeline green (lint, test, build, scan, deploy).
- Key Vault housing Cosmos connection replacement path (either MI or secret reference) implemented.
- Structured logging visible in Log Analytics (query returns JSON fields).

## 17. Appendices

### 17.1 Token Validation Contract

- aud must equal `api://<API_APP_ID>` (or raw appId if using that style).
- iss must match standard tenant or B2C issuer derived from policy.
- Required claims: `sub` (stable user id), `email` (optional fallback to `preferred_username`).

### 17.2 Pending Automation Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/prepare_env.sh` | Set azd env vars from .env template | Planned |
| `scripts/build_push.sh` | Deterministic docker build & push | Planned |
| `scripts/run_tests.sh` | Unified Python + JS test invocation | Planned |

---
Maintainer Handoff: After supplying the missing App Registration IDs and running `azd up`, follow Immediate Next Steps (Section 8). This document should be updated after each major milestone (use a short changelog at top on next revision).
