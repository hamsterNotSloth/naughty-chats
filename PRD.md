# Product Requirements Document (PRD)

Product Name: Naughty Chats (Clone of hottiechats.com)
Version: 0.1 Draft
Last Updated: 2025-09-12
Owner: Product / Founding Team
Related Docs: `screens.md`

---
## 1. Executive Summary
Naughty Chats is a web platform enabling users to discover or create AI-driven characters, engage in immersive NSFW (and optionally SFW) roleplay chats, and generate character-based images using prompt + preset driven workflows. The platform monetizes via a virtual currency (Gems) purchased in packs and consumed by AI chat messages and image generations. An affiliate system drives referral growth with a revenue share. This PRD defines the initial 0 → 1 implementation plus architectural and experiential guardrails to ensure scalability, safety, and extensibility.

Primary differentiators vs generic AI chat/generation tools:
- Character-centric model (persistent personas with traits + example dialogues)
- Unified economy across chat + images
- Discovery surfaces (Tavern) optimized for engagement velocity (popular, trending, fast load)
- Pose and quality presets for image generation reducing user cognitive load
- Growth levers: Discord funnel, affiliate %, free gem promotions
- Moderation strategy balancing speed & compliance

---
## 2. Problem Statement
Users seeking AI NSFW roleplay today face fragmented tools: chat-only bots lacking visual generation, or image models lacking persona continuity. They desire:
1. Persistent, richly-defined personas with predictable style/voice.
2. Fast iteration loops (low friction to begin chats or generate images).
3. A clear cost model (credits/gems) with transparency and fairness.
4. Tools to create, share, and iterate on characters with minimal technical skill.
5. Social discoverability to find high quality or trending personas.
6. Trust that harmful or disallowed content is filtered while still enabling adult freedom.

Opportunity: Combine these into a cohesive multi-modal experience with strong discovery and retention primitives.

---
## 3. Product Vision
Create the most engaging, safe, and extensible AI character universe for immersive adult (and optional safe) roleplay—where users can seamlessly move between narrative chat and visual depiction with minimal friction and predictable costs.

Vision Pillars:
- Expressive: Deep persona authoring (traits, dialogues, gallery) with future plugin extensions.
- Frictionless: Sub–3 second initial chat start; one-click generation with curated presets.
- Predictable: Transparent gem costs and quality tiers; clear balances & history.
- Safe-by-Design: Layered moderation without stifling legitimate consensual fantasy.
- Growth-Ready: Built-in attribution, referral, onboarding, upsell surfaces.
- Extensible: Modular architecture for future model providers, premium character marketplace.

North Star Metric (NSM): Weekly Retained Paying Creators (WRPC) – number of users who both created/maintained at least one character and spent gems (chat/gen) in a week.

Secondary Metrics: New Paying Users (NPU), Average Gems Spent per Active User (AGSAU), Character Engagement Depth (median messages per chat session), Image Generation Conversion (gens started / unique visits to generate page).

---
## 4. Goals & Non-Goals
### 4.1 Goals (MVP - Phase 1)
G1. Users can browse, search, and start a chat with a character in < 3 clicks.
G2. Users can create and publish a character with core metadata within 10 minutes.
G3. Users can generate images with at least 2 quality tiers and 6+ pose presets.
G4. Gem purchase, balance deduction, and ledger integrity enforced (no negative balances).
G5. Affiliate tracking and 15% commission attribution for purchases linked to referral codes.
G6. Moderation prevents disallowed categories and enables user reporting of characters, messages, and images.
G7. Latency targets: Chat response streaming begins < 2s p50; image generation job accepted < 1s p50.
G8. Basic analytics instrumentation for all major actions (see Metrics section).
G9. Users can favorite/subscribe to characters and access a consolidated favorites list in ≤ 2 clicks from any page.

### 4.2 Stretch (Phase 2+)
S1. Advanced prompt customization (negative prompts, seeds, variations).
S2. 2FA security + device/session management UI.
S3. Notifications center & web push.
S4. Multi-model provider abstraction.

### 4.3 Non-Goals (Initial MVP)
NG1. Mobile native apps (web responsive only initially).
NG2. Marketplace monetization for paid character assets.
NG3. Full localization / translation.
NG4. Complex real-time multi-user shared chat sessions.
NG5. Automated revenue share payouts beyond affiliate basics.

---
## 5. User Personas
| Persona | Summary | Primary Needs | Key KPIs Alignment |
|---------|---------|---------------|--------------------|
| Explorer | New user browsing trending characters | Fast discovery, low friction onboarding | Conversion to first chat & first gen |
| Roleplayer | Returns for immersive chat sessions | Reliable persona fidelity, low latency | Session length, retention |
| Creator | Authors characters for others | Easy creation tools, validation, visibility | Published characters, adoption rate |
| Visual Seeker | Primarily uses image gen | Control over style/pose, cost clarity | Image gen frequency, gem ARPU |
| Affiliate | Promotes platform off-site | Transparent stats, stable tracking | Referred signups, commission earned |
| Moderator/Admin | Enforces policies | Efficient review workflows, auditability | Time to action, backlog size |

---
## 6. Core User Journeys (Representative)
1. New Explorer (anonymous) → Browse Tavern → Click character → Prompt sign up → Complete sign up → Auto-return → Start chat.
2. Creator → Create Character Wizard (multi-step) → Publish → Character appears in Tavern → Receives usage stats.
3. Roleplayer → Open existing chat session → Send message → Stream reply → Rate response → Continue.
4. Visual Seeker → Generate page → Select character & pose → Input prompt → Choose 4 images @ Balanced → View results → Download.
5. Affiliate → Copy referral link → Share → Referral signs up → Makes purchase → Commission increases.
6. User with low gems → Attempt image generation → Insufficient gems modal → Navigate to Get Gems → Purchase → Retry generation.

---
## 7. Functional Requirements (FR)
Each FR has ID, Description, Priority (P0/P1/P2), Acceptance Criteria (AC). P0 required for MVP.

### 7.1 Navigation & Layout
- FR-001 (P0) Global top navigation with links: Explore, Roleplay (preview page), Tavern, Generate, Affiliate, Get Gems, Join Discord, Sign In/Up or User Menu.
  - AC: On mobile, nav collapses behind hamburger < 640px.
- FR-002 (P0) Display gem balance (authenticated) with real-time updates after transactions.
  - AC: Balance updates within 1s of gem ledger mutation (websocket or poll fallback 10s).

### 7.2 Authentication & Accounts
- FR-010 (P0) Email+password registration with age assertion and terms acceptance.
  - AC: Underage (configurable birth year threshold) -> rejection message.
- FR-011 (P0) Login with email/username + password.
  - AC: Incorrect credential attempt increments throttled counter; lock after N attempts with exponential backoff.
- FR-012 (P1) Password reset flow with email token (15 min expiry).
- FR-013 (P1) Email verification gating certain actions (publishing character, generating NSFW content) if config on.
- FR-014 (P2) Social auth providers (e.g., Google/Discord) optional.

### 7.3 Character System
- FR-020 (P0) Create Character Wizard (steps: Basics, Personality, Visuals, Tags, Visibility, Review).
  - AC: Autosave each step within 1s of field blur (debounced 500ms); restore after hard refresh.
- FR-021 (P0) Publish/Unpublish character toggle.
  - AC: Unpublished character 404s for other users.
- FR-022 (P0) Character listing API with filters: sort(popular|trending|new|recent|fast), tags[], nsfw flag, search query.
  - AC: Response time < 400ms p50 for cached popular queries.
- FR-023 (P0) Character detail view with example dialogues and gallery.
- FR-024 (P0) Favorite a character (toggle) & surface favorites/subscriptions list per user.
  - AC: Favoriting/unfavoriting reflects optimistic UI update then confirms via background sync; list accessible from user menu and character detail; API latency < 400ms p50; duplicates prevented idempotently.
- FR-025 (P2) Character rating (explicit star) aggregated.

### 7.4 Chat / Roleplay
- FR-030 (P0) Start chat session for a character -> sessionId.
  - AC: API returns within 600ms p50.
- FR-031 (P0) Send user message; receive streaming AI response tokens.
  - AC: First token < 2s p50; final latency < model SLA.
- FR-032 (P0) Gem cost deduction per AI response (predictive estimate visible pre-send if possible).
  - AC: If insufficient balance, message blocked; upsell modal shown.
- FR-033 (P1) Regenerate last AI message (cost re-applied; original kept in history variant chain or replaced depending config).
- FR-034 (P1) Rate AI message (thumbs or simple positivity metric).
- FR-035 (P2) Export chat transcript (sanitized JSON / text).

### 7.5 Image Generation
- FR-040 (P0) Submit generation job with prompt, characterId optional, posePreset, count(1|4|9), orientation, style, quality tier.
  - AC: Job accepted -> status=QUEUED with position if non-zero backlog. Live gem cost preview recalculates instantly (<=150ms client) when user changes quality tier or count before submission; disabled (shows spinner) if pricing config fetch older than 5 minutes triggers refetch.
- FR-041 (P0) Poll or subscribe for generation job progress & final images.
  - AC: Completed images accessible within job object or separate listing endpoint.
- FR-042 (P0) Display thumbnails & open full-size with metadata (seed, promptFinal, quality tier).
- FR-043 (P0) Handle partial failures (some images fail) -> show distinct status + refund partial gem cost.
- FR-044 (P1) Cancel queued job prior to processing start.
- FR-045 (P2) Negative prompt / advanced panel.

### 7.6 Economy / Gems
- FR-050 (P0) Gem pack catalog with server-authoritative price & currency.
- FR-051 (P0) Purchase flow via payment provider (e.g., Stripe) with webhook reconciliation.
  - AC: Duplicate webhook events idempotent.
- FR-052 (P0) Ledger of gem transactions (paginated) with balance-after calculations.
- FR-053 (P0) Gem deduction atomic operations (optimistic UI followed by reconcile or rollback on failure).
- FR-054 (P1) Promo code application with discount or bonus gems.
- FR-055 (P2) Time-limited free gem event banners.

### 7.7 Affiliate Program
- FR-060 (P0) Generate referral code per approved user (or auto-enable all users).
- FR-061 (P0) Track clicks, signups, purchase conversions attributable to referral code (last-click logic with cookie window; default 30 days).
- FR-062 (P0) Display affiliate dashboard metrics: clicks, signups, purchases, commission pending/paid.
- FR-063 (P1) Withdrawal request workflow (manual processing in MVP).
- FR-064 (P2) Fraud detection heuristics (IP clustering flagging).

### 7.8 Moderation & Reporting
- FR-070 (P0) Prompt & output text moderation (pre-display filter; block & notify user).
- FR-071 (P0) Image moderation (asynchronous; retroactive removal + refund if violation confirmed).
- FR-072 (P0) User report submission for character, message, image, user.
- FR-073 (P1) Admin moderation queue UI.
- FR-074 (P1) Soft-delete with reversible state for 7 days.

### 7.9 Notifications (Phase 2 base)
- FR-080 (P1) Inline toasts for key events (generation complete, insufficient gems, moderation block).
- FR-081 (P2) Persistent notification center with mark-read.
- FR-082 (P2) Web push for generation completion.

### 7.10 System Status & Banners
- FR-090 (P0) Global status banner for downtime or degradation.
- FR-091 (P1) Admin-configurable incident creation API.

### 7.11 Analytics & Instrumentation
- FR-100 (P0) Event tracking pipeline for defined event inventory.
- FR-101 (P0) Unique user session identification (anonymous -> persists through signup for attribution linking).
- FR-102 (P1) A/B experiment flag service integration.

### 7.12 Security & Privacy
- FR-110 (P0) Age gate self-attestation for NSFW gating.
- FR-111 (P0) TLS enforced; cookies HttpOnly, Secure, SameSite=Lax (or Strict for auth).
- FR-112 (P0) Content sanitization (HTML stripping) for user bios and dialogues.
- FR-113 (P0) Rate limiting (IP + user) for auth & generation endpoints.
- FR-114 (P1) Data export (JSON) + account deletion (soft then purge). 
- FR-115 (P2) 2FA (TOTP) optional.

### 7.13 Accessibility
- FR-120 (P0) Keyboard navigation for all interactive elements.
- FR-121 (P0) Non-text contrast ratio ≥ 3:1 for UI components.
- FR-122 (P0) Live regions for streaming chat & generation progress.
- FR-123 (P1) Reduced motion mode (respect prefers-reduced-motion).

### 7.14 Discovery & UX Enhancements
- FR-124 (P0) Trending tags & character carousel on home/Tavern.
  - AC: Updated at least every 5 minutes from cached aggregate; click navigates to filtered tavern view.
- FR-125 (P1) Starter prompt templates (e.g., "Flirty Introduction", "Conflict Twist") selectable when opening chat.
  - AC: Selecting template pre-fills user message box without auto-sending.
- FR-126 (P0) NSFW content interstitial (first time per session) confirming age & consent before revealing explicit thumbnails.
  - AC: Dismiss persists via localStorage + server flag for logged-in users; accessible focus management.
- FR-127 (P1) Suggested prompts generated dynamically from character traits (max 3, regen button cooldown 10s).
  - AC: API latency < 800ms p50; fallback to static templates on timeout.
- FR-128 (P2) Prompt history recall (last 10 user prompts per character) with quick insert.
  - AC: Stored client-side encrypted or server-side linked to session depending privacy config.
- FR-129 (P2) Batch image download (.zip) for a completed generation set.
  - AC: Zip generation streamed; size limit 50MB.
- FR-130 (P1) Credits / Attribution page listing model sources, CivitAI style presets, and open-source licenses.
  - AC: Accessible from footer; includes version hashes and license slugs.

---
## 8. Non-Functional Requirements (NFR)
| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | Chat first token latency | <2s p50, <4s p90 |
| Performance | Image job accept API | <600ms p50 |
| Performance | Character list API | <400ms p50 cached |
| Availability | Uptime (core APIs) | 99.5% MVP |
| Scalability | Horizontal scale pods/chat workers | Linear until 10x baseline |
| Security | No plaintext PII at rest | 100% encrypted or hashed |
| Privacy | Data export SLA | <7 days |
| Moderation | Report triage initial response | <24h |
| Observability | Error budget SLO burn alerts | 4h detection |
| Accessibility | WCAG 2.1 compliance | Level AA core flows |
| Reliability | Duplicate payment webhook handling | Idempotent proven in test |
| Cost | AI inference cost / revenue ratio | ≥ 45% gross margin |

Additional NFR Details:
- Backpressure: Queue length > X triggers quality tier throttle banner.
- Caching: CDN for static assets; edge caching for character summaries (TTL 60s, stale-while-revalidate).
- Logging: Structured JSON with correlation IDs; PII minimization.
- Disaster Recovery: Daily encrypted backups of primary DB; RPO 24h, RTO 4h.

---
## 9. Data Architecture Overview
(See `screens.md` for entity fields.) Key principles:
- Separation of hot (chat sessions, jobs) vs warm data (ledger, reports) using primary DB + analytics warehouse (later).
- Event sourcing for gem transactions (append-only ledger drives balance derivation).
- WebSocket multiplex channel for chat + generation updates (namespaced events: chat.*, gen.*).

### 9.1 Technology Stack & Deployment Architecture
Frontend:
- Next.js (App Router) for SSR/ISR of public discovery pages (Tavern, Character Detail) + client-side hydration for interactive chat & generation flows.
- Component library: Tailwind CSS + Headless UI (or Radix) for accessible primitives.
- State mgmt: Lightweight (React Query for server state, minimal local Zustand slice for ephemeral UI) – avoid over-engineering early.
- Image optimization & edge caching leveraged via Next.js Image component + Azure CDN.

Backend (Core API):
- Python (FastAPI) for high concurrency async endpoints (chat session management, character CRUD, gem ledger, moderation hooks).
- Separate internal worker process (Celery or custom asyncio workers) for queued image generation status reconciliation & moderation scanning.
- Authentication: JWT (short-lived access) + HttpOnly refresh cookie rotation; session continuity sync with WebSocket auth token refresh endpoint.

AI Model Inference:
- RunPod deployments for both LLM (chat) and diffusion-based image generator pods.
- Abstraction layer (ModelService) exposing: generate_chat_reply(), submit_image_job(), cancel_job().
- Model metadata & style inspiration may reference community models from CivitAI; store curated whitelist with version / license notes to ensure compliance (no direct automatic pulling of unvetted models at MVP).
- Safety: Pre / post prompt filters and negative prompt injection (Phase 2 advanced customization) prior to sending to RunPod endpoints.
- Provenance & Audit: Persist model identifier (provider, version hash) with each message/image for future reproducibility & A/B cost analysis.
- Attribution: For any CivitAI-derived style preset, record source model name + license slug and surface attribution in Credits / About page (Phase 1 minimal text list, Phase 2 richer links).
- Dynamic Throttling: If queue depth or average token latency > threshold, degrade to lower-cost model automatically with user banner (Phase 2).

Data Stores:
- Primary OLTP DB: Cosmos DB (Azure Cosmos DB Core SQL API) – entities: users, characters, chats, messages, images, gem_ledger, affiliate_referrals, moderation_items.
- Object Storage: Azure Blob Storage for generated images & prompt logs (sanitized), with signed URL delivery.
- Search/Discovery (Phase 2+): Optional Azure Cognitive Search or Cosmos DB-backed search/indexing for character & tag search initial.

Messaging / Async:
- Internal queue (Azure Service Bus) for image job lifecycle events (QUEUED → PROCESSING → COMPLETE/FAILED) and moderation tasks.

Deployment Targets:
- Frontend: Azure Static Web Apps or Azure App Service (SSR) depending on need for server-side auth headers. (Decision: start with App Service for unified domain + custom headers.)
- Backend API & workers: Azure Container Apps (separate revisions for api / worker) with autoscaling on CPU + concurrent websocket connections.
- WebSocket endpoint served from same FastAPI container (uvicorn) behind reverse proxy (NGINX or Azure Front Door) – sticky session not required due to stateless token auth.

Payments:
- Primary payment integration will use either zkp2p or phyziro (web3 / alt payment) – final selection TBD (see Open Questions). Fallback: Stripe standard card processing (kept optional if compliance / KYC friction appears).
- Pluggable PaymentProvider interface enabling run-time feature flag to select active provider & support phased rollout.

Observability:
- Logging: Structured JSON -> Azure Log Analytics workspace.
- Metrics: Prometheus scraping (Container Apps) forwarded to Azure Monitor; key custom metrics (chat_first_token_latency, image_job_duration, queue_depth, model_cost_per_token).
- Tracing: OpenTelemetry (FastAPI + workers) exporting traces → Azure Application Insights.

Security & Secrets:
- Secrets stored in Azure Key Vault (DB creds, provider API keys, RunPod tokens).
- Per environment (dev/staging/prod) isolated resource groups; principle of least privilege service principals with managed identity for container apps pulling secrets.

CI/CD:
- GitHub Actions pipeline: lint -> test -> build docker images -> push to Azure Container Registry -> deploy to Container Apps; separate job for Next.js build & deploy.
- Infrastructure as Code: Bicep or Terraform (Phase 1 choose Bicep) templates under `infra/` (future addition) for reproducibility.

Scalability & Performance Notes:
- Horizontal scale: Additional API replicas when p95 latency > target or active websocket connections > threshold.
- Image generation: Burst scaling by provisioning additional RunPod replicas; queue length > N triggers UI banner & dynamic cost adjustments (future).
- CDN caching for character list (stale-while-revalidate) to achieve sub-400ms latency target globally.

Compliance & Licensing:
- CivitAI referenced models must have permissive license & adult content allowance; store license slug in DB for each curated preset style.
- Maintain audit log of moderation overrides & model version changes.

Failure Domains & Resilience:
- Circuit breakers on model inference calls (fast-fail & fallback to apology message; gem refund on failure).
- Graceful degradation: If image service degraded show banner & disable high-quality tier.
- Retry policy: Exponential backoff (max 3) for webhook reconciliations & RunPod job status fetch.

---
## 10. Analytics, Metrics & Instrumentation
### 10.1 Core KPIs
| KPI | Definition | Target (MVP exit) |
|-----|------------|------------------|
| WRPC | Weekly retained paying creators | Establish baseline (Goal: upward trend) |
| NPU | New paying users / week | 200 (illustrative placeholder) |
| Gem Purchase Conversion | Purchases / Get Gems visits | >12% |
| Image Gen Conversion | Users generating / visits to generate page | >35% |
| Chat Depth | Median messages per active chat session | >8 |
| Character Adoption | % of created characters with ≥5 external sessions in 7 days | >30% |
| Referral Contribution | % revenue from affiliate referrals | 10–20% |

### 10.2 Instrumentation Matrix (Sample)
| Event | Properties | Purpose |
|-------|------------|---------|
| chat.session_start | characterId, sessionId, entryPoint | Funnel & retention |
| chat.message_send | length, gemsPredicted | Cost modeling & abuse detection |
| chat.message_receive | tokens, gemsActual | Model efficiency tracking |
| gen.start | quality, count, posePreset | Feature usage & cost forecasting |
| gen.complete | images, duration | Success rate, latency |
| gems.checkout_start | packId, price | Conversion drop-off |
| gems.checkout_success | packId, amount, currency | Revenue tracking |
| tavern.search | queryLength, tagCount | Search efficacy |
| character.create_step | step, error? | Wizard friction |
| report.submit | targetType, reasonCode | Moderation load |
| affiliate.copy_link | | Growth efficacy |
| tavern.trending_click | tag or characterId | Discoverability impact |
| chat.template_select | templateId | Starter prompt adoption |
| chat.suggested_prompt_click | suggestionId | Dynamic suggestion utility |
| chat.prompt_history_reuse | priorPromptHash | Re-engagement metric |
| interstitial.nsfw_accept | sessionId | Compliance gating effectiveness |
| gen.batch_download | imageCount | Power user feature usage |
| credits.view | referrer | Attribution transparency |

### 10.3 Experimentation (Phase 2)
- Add feature flag service (remote config) gating: new quality tiers, regeneration UI variant, onboarding flows.
- Bucketing: deterministic hash on userId.

---
## 11. Competitive & Differentiation Notes
- Generic AI chat apps: Lack integrated image pipeline or character economy.
- Image-only generators: Shallow persona persistence; users manually craft long prompts.
- Opportunity: Reduce friction via structured persona + pose presets + unified credit system.

---
## 12. Release Phasing & Roadmap
### Phase 1 (MVP ~8–10 weeks)
Scope: FR P0 set (Auth, Character create/list/detail, Favorites/subscriptions, Chat basic streaming, Image gen baseline (FR-040..043), Gem purchase, Affiliate basic, Reporting, Status banner, Core moderation screens minimal, Analytics pipeline baseline, Trending tags/carousel (FR-124), NSFW interstitial (FR-126)).
Deliverables: Production deploy behind invite code if needed.
### Phase 2 (Engagement & Safety Enhancements)
Scope: Regenerate, Ratings, Cancel image jobs, Promo codes, Notifications toasts, Admin moderation UI, Partial advanced prompts, Starter prompt templates (FR-125), Suggested prompts (FR-127), Credits / Attribution page (FR-130).
### Phase 3 (Growth & Personalization)
Scope: Notification center, Web push, Experiment framework, 2FA, Favorites surfacing algorithmic ranking, Advanced moderation automation, Prompt history recall (FR-128), Batch image download (FR-129).
### Phase 4 (Scale & Monetization Expansion)
Scope: Marketplace, multi-model selection, localization groundwork, performance deep optimizations, advanced creator monetization.

Dependencies & Sequencing:
- Payments before ledger-dependent features (affiliate payouts, ledger UI).
- Moderation baseline before opening public character creation broadly.
- Analytics baseline before growth experimentation.

---
## 13. Risks & Mitigations
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| AI model drift increases per-message cost | Margin erosion | Med | Monitor cost per token & dynamic pricing guardrails |
| Abuse of NSFW boundaries / policy violations | Legal / platform risk | High | Multi-layer moderation + rapid takedown workflows |
| Payment fraud / chargebacks | Revenue loss | Low-Med | Provider risk scoring + delayed large withdrawal settlements |
| Affiliate fraud (self-referrals, bot traffic) | Commission leakage | Med | IP/device fingerprint checks & anomaly detection |
| Latency spikes under load | User churn | Med | Autoscale + circuit breakers + backpressure messaging |
| Data breach exposure (PII) | Compliance damage | Low | Encryption, least privilege, secret rotation |
| Model jailbreak attempts | Policy evasion | High | Prompt sanitization, output classifier, red-team tests |
| Negative prompt absence leads to churn for advanced users | Lost power users | Med | Prioritize optional advanced panel in Phase 2 |
| Overbuilding v1 causing delays | Time-to-market slip | Med | Strict P0 scope discipline + weekly scope review |

Open Questions:
1. Exact disallowed content taxonomy & escalation SLA.
2. Minimum withdrawal threshold for affiliate commissions.
3. Refund policy for chat response dissatisfaction (if any).
4. How to treat multi-tab simultaneous chat sessions cost-wise.
5. Geographic restrictions for payments & NSFW access.

Assumptions:
- Stripe (or equivalent) as initial payment provider.
- Single primary LLM + image model provider at MVP (abstract layer future).
- Core user base English-speaking at launch.
- Evaluating decentralized / alt payment rails (zkp2p vs phyziro) for lower fees & global reach; abstraction layer will allow switching without core gem ledger changes.

---
## 14. Success Criteria (MVP Exit)
- >= 40% Day 7 retention of users who performed both a chat and a generation on Day 0.
- >= 12% conversion from first gem purchase prompt to completed checkout.
- <= 5% moderated removal rate for published characters (after initial 2-week stabilization).
- <= 2% failed image job rate (excluding user-canceled).
- >= 95% moderation decision SLA < 24h.
- Zero negative gem balance incidents in production logs.

---
## 15. Appendices
### 15.1 Terminology
(Refer to Glossary in `screens.md`.)

### 15.2 Traceability Matrix (Excerpt)
| FR ID | Screen / Flow | Analytics Event(s) | NFR Link |
|-------|---------------|--------------------|----------|
| FR-020 | Character Creation Wizard | character_create.step_view | Performance (autosave) |
| FR-031 | Chat Session | chat.message_send / chat.message_receive | Perf latency target |
| FR-040 | Image Generation | gen.start / gen.complete | Availability, cost |
| FR-052 | Gems Ledger | gems.ledger_view | Integrity, reliability |
| FR-060 | Affiliate Dashboard | affiliate.view | Growth |

### 15.3 Future Extensions (Out of Scope)
- Paid premium character marketplace tier splits.
- Creator revenue share beyond affiliate scope.
- Multi-language character translation pipeline.
- VR/immersive chat experiences.

---
End of PRD.
