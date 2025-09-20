Backend Plan — Naughty Chats

Purpose

This document is the authoritative, executable plan for the backend work required to deliver the MVP described in the PRD. It covers architecture decisions, data model drafts, API surface, core algorithms (especially gem ledger and atomic deductions), worker topology for chat/image generation, moderation, observability, infra, CI/CD, testing, rollout milestones, risks and mitigations.

Audience

Product, Backend Engineers, DevOps, Security, and QA.

Constraints & Assumptions

- Primary cloud: Azure (Cosmos DB, Blob Storage, Container Apps, Key Vault, Azure Service bus). Where alternatives matter, notes are provided.
- Backend framework: FastAPI (async-first) as stated in PRD.
- Workers: Async workers (Celery with Azure Service Bus broker or custom asyncio worker using Service Bus) — choice documented below.
- Model providers: RunPod (or other external model provider). All calls must be abstracted behind a ModelService interface.
- Payment provider: Start with Stripe as fallback/default for MVP; design PaymentProvider interface.
- Must support NSFW content flows but gated with age verification and layered moderation.
- Strong requirement for ledger integrity (no negative balance), idempotent webhooks, and deterministic refund behavior.

High-level Architecture

- API (FastAPI) behind Azure Front Door / Application Gateway.
  - Auth, Character CRUD, Chat session bootstrap, Generation job submission, Gems/purchase endpoints, Affiliate tracking, Moderation endpoints.
- Realtime channel for chat & generation status: WebSocket (primary) with fallback SSE for environments where WS unsupported. Auth handshake via short-lived token from API.
- ModelService: Adapter layer to call LLM and image provider(s) with unified interface and adapter implementations for RunPod, OpenAI, or on-prem later.
- Worker pool(s): Independent horizontally-scaling workers for:
  - Chat inference orchestration (if proxying streaming from provider, this may be lightweight; if orchestrating model calls, must scale accordingly).
  - Image generation job reconciliation and storage upload.
  - Moderation scanning (async image checks, heavy processing).
- Queue: Azure Service Bus (durable topics/queues) for image job lifecycle and background tasks. Service Bus is the only supported queue implementation in production;
- Persistence: Cosmos DB (Core SQL API) + Azure Blob Storage (images + large artifacts). No additional caching layer for MVP; rely on Cosmos DB and Azure-native services.
- Observability: OpenTelemetry traces, Prometheus metrics (or Azure Monitor exporters), structured JSON logs to Log Analytics.

Component Plan

1) API Gateway & Routing

- Use Azure Front Door (or App Gateway) to terminate TLS, provide WAF rules and route to container apps.
- Public endpoints: /api/v1/... with versioning.
- Internal endpoints for workers: /internal/... protected by mTLS or managed identity.

2) Authentication & Sessions

- Flow: JWT access token (short lived, e.g., 15m) + HttpOnly refresh cookie (rotating opaque refresh token). Use refresh token rotation pattern.
- WebSocket auth: client requests short-lived ws_token from POST /api/v1/ws/auth -> server returns ws_token (exp 1m). Client connects to ws endpoint passing token in query header.
- Account lockout on N failed attempts; exponential backoff. Implement failed_login counter using Cosmos DB with TTL or Azure Table Storage to maintain counters.
- Email verification gating: require verified email for publishing characters and NSFW generation if config enabled.

3) Data Modeling (draft tables and key columns)

Note: these are drafts to be converted into migration files (alembic or similar). Focus on indexes, constraints and immutability where required.

- users
  - id uuid pk
  - email text unique not null
  - username text unique not null
  - password_hash text
  - birth_year int
  - email_verified boolean default false
  - roles jsonb (or enum)
  - created_at timestamptz
  - last_active timestamptz

- characters
  - id uuid pk
  - author_id uuid fk -> users
  - name text
  - slug text unique
  - short_description text
  - bio text
  - tags text[]
  - nsfw_level smallint
  - published boolean
  - created_at timestamptz
  - metadata jsonb (persona prompts, memory pointers)

- chats
  - id uuid pk
  - session_id uuid unique
  - user_id uuid nullable (guest sessions if allowed)
  - character_id uuid
  - created_at
  - last_message_at
  - status enum (active, archived)

- messages
  - id uuid pk
  - chat_id fk
  - sender enum (user, ai, system)
  - content text
  - tokens integer
  - model_id text
  - created_at
  - moderation_status enum
  - metadata jsonb

- gem_ledger (append-only event store)
  - id bigserial pk
  - user_id uuid indexed
  - change integer not null (positive for credit, negative for debit)
  - balance_after bigint not null -- optional cache column, but must be validated
  - event_type text (purchase, debit, refund, promo, admin_adjust)
  - reference_id uuid nullable (e.g., order_id, chat_message_id, gen_job_id)
  - idempotency_key text nullable
  - created_at timestamptz default now()
  - metadata jsonb

Design note: Use event-sourced ledger. Balance derivation is SUM(change) grouped by user ordered by created_at (or id). For performance, maintain a per-user cached balance in users.gem_balance (denormalized) updated transactionally with ledger insert via serializable tx or advisory lock.

- gen_jobs
  - id uuid pk
  - user_id
  - character_id nullable
  - prompt text
  - pose text
  - count int
  - quality text
  - status enum (queued, processing, completed, failed, canceled)
  - estimated_cost int
  - actual_cost int
  - position int nullable (queue pos stored in Service Bus metadata or Cosmos DB)
  - result jsonb (image ids, urls)
  - created_at
  - updated_at

- images
  - id uuid
  - job_id fk
  - url text
  - thumb_url text
  - seed text
  - safety jsonb
  - size text
  - created_at

- affiliates
  - id uuid
  - user_id
  - code text unique
  - clicks bigint
  - signups bigint
  - purchases bigint
  - commission_pending bigint
  - created_at

- moderation_items
  - id uuid
  - item_type enum (message, image, character)
  - item_id uuid (fk to messages/images/characters)
  - status enum (pending, reviewed, actioned)
  - reason text
  - created_at

- webhooks (for idempotency tracking)
  - id serial
  - provider text
  - provider_event_id text unique
  - processed boolean
  - payload jsonb
  - created_at

Indexes and perf notes

- Index gem_ledger on (user_id, id DESC) to fetch latest balance quickly.
- Partial indexes for gen_jobs where status IN ('queued', 'processing') to speed dashboard queries.
- messages: index chat_id + created_at for fast streaming.
- characters: GIN index on tags and metadata for search.

4) API Surface (high level)

Design with OpenAPI-first. Provide examples here; later produce full spec file.

Auth
- POST /api/v1/auth/register { email, username, password, birthYear, refCode? } -> 201 { user, accessToken, refreshCookie }
- POST /api/v1/auth/login { identifier, password } -> { accessToken, set-cookie refresh }
- POST /api/v1/auth/refresh -> rotates refresh cookie and returns new access token.
- POST /api/v1/auth/logout -> invalidate refresh token.
- POST /api/v1/auth/password-reset/request { email }
- POST /api/v1/auth/password-reset/confirm { token, newPassword }

Characters
- GET /api/v1/characters?sort=&tags=&nsfw=&q=&limit=&cursor=
- GET /api/v1/characters/:id
- POST /api/v1/characters (auth) - multi-step autosave endpoints PATCH /api/v1/characters/:id/step
- POST /api/v1/characters/:id/publish
- POST /api/v1/characters/:id/favorite

Chat
- POST /api/v1/chat/sessions { characterId } -> { sessionId }
- POST /api/v1/chat/sessions/:id/message { content, clientMetadata } -> streams tokens via WS / SSE or returns a job id if async.
- POST /api/v1/chat/sessions/:id/regenerate { lastMessageId }
- POST /api/v1/chat/sessions/:id/rate { messageId, rating }
- GET /api/v1/chat/sessions/:id/history?limit=

Generation
- POST /api/v1/generate { characterId?, prompt, pose, count, quality } -> { jobId, estimatedCost }
- GET /api/v1/generate/jobs/:id -> job object
- GET /api/v1/generate/jobs?status=queued,processing
- POST /api/v1/generate/jobs/:id/cancel

Gems & Payments
- GET /api/v1/gems/packs
- POST /api/v1/gems/checkout { packId, provider } -> { checkoutUrl }
- POST /api/v1/gems/webhook (provider) -> idempotent handler
- GET /api/v1/gems/ledger?cursor=&limit=
- POST /api/v1/gems/apply-promo { code }

Affiliates
- GET /api/v1/affiliates/me
- GET /r/:code -> landing + set cookie

Moderation
- POST /api/v1/moderation/report { itemType, itemId, reason }
- GET /api/internal/moderation/queue (admin)

Internal / Worker
- POST /internal/jobs/gen/reconcile (secured)
- POST /internal/model/callbacks (secured)

5) Gem Ledger: design & invariants

Requirements
- No negative balances.
- All ledger writes immutable and append-only with idempotency keys to handle retries.
- Balance derivable by summing events, but also maintained as a denormalized value for fast checks.
- Atomic deduction must be safe under concurrency.

Chosen approach for Cosmos DB
- Use per-user partitioning in Cosmos DB (partition key = user_id) so all ledger events for a user live in the same partition. Leverage Cosmos DB transactional batch (or stored procedure) to atomically append a ledger event and update the user's cached balance within the same partition. This provides ACID semantics within that partition.

Workflow (Cosmos DB transactional batch)
  1. Read user's balance document (or include it in partition) in the transactional batch.
  2. Compute new_balance = current_balance + change. If new_balance < 0 -> abort and return insufficient funds.
  3. Append new ledger event document with metadata and idempotency_key.
  4. Update user's balance document with new_balance.
  5. Commit batch — all operations succeed or none are applied.

Idempotency & reconciliation
- All external events (payment provider webhooks) include the provider_event_id used to dedupe inserts. If a conflicting idempotency_key exists, return the prior result.
- Periodic reconciliation job will scan ledger partitions and recompute balances to validate and repair cached balances if drift is detected.

Cosmos DB pseudocode (python + azure-cosmos)

# within same partition (user_id)
from azure.cosmos import TransactionalBatch
batch = container.create_transactional_batch(partition_key=user_id)
# optionally read current balance from a dedicated balance doc or from a pre-fetched value
# add operations in batch: create ledger event, replace balance doc
batch.create_item(ledger_event_doc)
batch.replace_item(balance_doc_id, updated_balance_doc)
response = batch.execute()
if not response.get_success():
    raise InsufficientBalance

Notes: ensure partition key design keeps all user-specific ledger operations within the same partition; avoid cross-partition transactional needs.

6) Chat session & streaming design

Goals
- First token p50 < 2s for streaming; ensure quick bootstrap.
- Rate limit per user and per IP.
- Cost estimation prior to send.

Flow
- Client POST /chat/sessions { characterId } -> server creates sessionId and returns model prompt template + predictive cost estimate based on model and token budget.
- Client sends message: POST /chat/sessions/:id/message -> server performs pre-send moderation (quick filter), checks gem balance (using advisory lock read-only or read cached balance), reserves an estimated cost hold (optional) by inserting a reserved ledger event (type=hold) with negative change.
- Server enqueues message to chat worker if model call is asynchronous, or forwards to ModelService which streams tokens.
- Streaming via WebSocket events: token_delta, partial_text, message_complete, error.
- On message_complete: compute actual cost (e.g., tokens used * cost per token), adjust ledger: either convert hold to final debit (update metadata) or insert additional debit or refund difference atomically.
- If balance insufficient at send: block and return error modal content.

Regenerate behavior
- Regenerate either consumes cost equal to a full new message; original message kept in history and marked variant chain. Provide option to replace variant with new one under certain configs.

7) Image generation job lifecycle

Flow
- POST /api/v1/generate -> validate prompt, compute estimated_cost = pricing_matrix(quality, count). Check balance via ledger transactional append and reject if insufficient.
- Push job to queue (Azure Service Bus). Return jobId and queue position (approx) using Service Bus message sequencing/peek metrics.
- Worker picks job from Service Bus, updates job.status -> processing, sends request to ModelService.submit_image_job (RunPod). Worker receives callback or polls provider job status.
- On provider completion: download images, upload to Azure Blob Storage (private container), create image records in Cosmos DB, set job.status = completed, set actual_cost and transfer hold -> final debit: convert hold event into debit or insert final debit + refund difference.
- On failure: job.status = failed; refund full hold.
- Partial success: job.status = completed_partially; compute refund for failed images and insert refund ledger event.

Queue design & scaling
- Use Azure Service Bus with topics/queues and consumer groups. Use durable messages, dead-lettering, and message lock/renew semantics to handle crashes and retries. Scale workers by adding Container App replicas subscribed to Service Bus.
- Maintain a lightweight job index in Cosmos DB for quick user queries of queue state.

8) Moderation

- Pre-send (sync) text filter: quick regex + lightweight classifier to block obvious disallowed content (underage, illegal content, doxxing, sexual content involving minors). Run inline before sending to model.
- Post-generation image moderation: async heavy scanner (AI-based) that classifies images; flagged images create moderation_items and may trigger refund and removal.
- Human review: moderation queue (internal UI) for items above certain severity or appeals.
- Logs: store moderation decisions with references to message/image and model provenance (model id, promptFinal) for audit.

9) Payments & affiliate tracking

- Checkout: server creates an order, stores expected gem_amount with idempotency_key, redirects to provider checkout session.
- Webhook: idempotent processing using provider event id recorded in webhooks table. On successful payment: insert gem_ledger event crediting user with gems, update affiliate referrer commission as pending.
- Affiliate attribution: set cookie r=<code> with 30-day TTL on landing routes. During user signup/purchase check referral cookie and attribute last_click.
- Provide reconciliation scripts to compare provider reports vs ledger sums.

10) Observability & SLOs

Key metrics (Prometheus / Azure Monitor):
- chat_first_token_latency (histogram)
- chat_message_total_tokens
- gen_job_accept_latency
- gen_job_completion_time
- gen_queue_depth
- gem_ledger_failures
- webhook_processing_time
- error_rate_5m

Tracing
- Instrument FastAPI + workers with OpenTelemetry. Sample traces for long-running jobs and failed flows.

Logging
- Structured JSON logs including correlation_id for requests. Correlation_id must be set at API gateway and propagated.

Alerts / Dashboards
- Alert on gen_queue_depth > threshold for N minutes, chat_first_token_p95 > target, error rate > SLO.

11) Security & Compliance

- Secrets in Key Vault; services access via managed identity.
- TLS everywhere; cookies HttpOnly + Secure + SameSite=Lax.
- PII minimization: do not store raw payment details. Prompt logs must be sanitized if containing PII; consider redaction for logs and storage.
- Rate limiting on auth, chat message, generate endpoints (IP + user based) — implement using Cosmos DB counters or Azure API Management rate-limiting policies.
- Penetration testing before public launch.

12) CI/CD & IaC

- GitHub Actions: unit tests, lint, build docker image, push to ACR, deploy to Container Apps via azure/cli or GitHub azure/actions.
- IaC: Bicep templates for Cosmos DB, Container Apps, Blob Storage, KeyVault, Front Door. 
- Migration: data migration scripts for Cosmos DB (document versioning and transforms) with reviewable PRs.

13) Testing strategy

- Unit tests for all business logic (ledger ops, cost calculations, moderation heuristics).
- Integration tests with a test Cosmos DB emulator or a dedicated test Cosmos account and Azure Service Bus (or emulator) running in GH actions.
- Contract tests for ModelService adapters via recorded VCR-like fixtures.
- E2E tests for major flows (signup -> buy gems -> start chat -> generate image).
- Load testing: simulate chat tokens and image jobs; ensure queue scales and alerts firing.

D. Useful libraries & tools

- FastAPI, uvicorn, pydantic
- async drivers for Cosmos DB (azure-cosmos)
- Azure Service Bus client libraries
- Celery alternatives: use Azure Functions / Container Apps workers subscribing to Service Bus.
- opentelemetry-instrumentation, prometheus-client
- pytest + pytest-asyncio

End of plan

---

16) Azure Deployment Plan (moved)

The detailed Azure deployment plan has been moved to `deployments.md` at the repository root. See `deployments.md` for the full Azure-specific infrastructure, runbooks, CI/CD, and cost controls.

End of plan
