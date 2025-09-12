# Screens & Feature Specification (Clone of hottiechats.com)

Version: 0.1 (Foundational Specification)
Last Updated: 2025-09-12
Authoring Purpose: Internal product + engineering reference for building a functional clone with extensibility, compliance, analytics, and scalability in mind.

---

## 1. Global System Overview

The product is an AI-assisted NSFW roleplay + character discovery + image generation web platform with a virtual currency economy ("Gems"), affiliate commissions, and user-generated character assets. Core pillars:

1. Character Layer – Creatable, browsable, taggable persona entries with metadata and media.
2. Roleplay / Chat Layer – Conversational interface for interacting with character AIs (likely streaming responses, token budgets, rating loops).
3. Image Generation Layer – Prompt-to-image workflow with selectable character context, poses, styles, qualities, queue states, credit consumption.
4. Economy Layer – Gems purchase, balance deduction for chats / generations, rewards, affiliate commissions, referral bonuses, free gem promotions.
5. Community / Discovery – Tavern (character discovery hub), trending, popular, new, recent, search, user curation, tagging, filters.
6. Growth & Retention – Discord CTA, affiliate program, onboarding prompts, email notifications, push (optional), churn prevention.
7. Trust & Safety – Moderation of characters, generated content, user reports, flagged metadata, rate limiting, content filtering for prohibited categories.
8. Observability – Feature-level analytics + performance instrumentation + A/B testing scaffolding.

---

## 2. Global UI Architecture & Shared Components

| Component | Description | Key Props / Data | States | Notes |
|-----------|-------------|------------------|--------|-------|
| Top Navigation Bar | Persistent site-wide nav with logo & primary links | userSession, gemBalance, unreadNotifications | Authenticated / Guest / Loading | Collapses on mobile (hamburger) |
| Primary Links | Explore, Roleplay, Tavern, Generate, Affiliate, Get Gems, Join Discord | routeKey | Active / Hover / Disabled | "Get Gems" highlighted (CTA) |
| Auth Buttons | Sign In / Sign Up OR Avatar Menu | userSession | Loading / Authenticated / Guest | Avatar dropdown includes Settings, Profile, Logout |
| Search Bar (Global optional) | Quick search for characters | query, suggestions[] | Idle / Typing / Results / Empty / Error | Debounce 300ms, keyboard accessible |
| Toast / Snackbar | Inline notifications (success, error, info) | type, message, actionLabel, timeout | Visible / Dismissed | ARIA live region |
| Modal Wrapper | Reusable portal container | isOpen, onClose, size | Enter / Exit / Hidden | Focus trap |
| Tag Chip | Visual tag element | label, isSelected | Active / Inactive / Hover | Click filter semantics |
| Character Card | Represents a character in grids | id, name, avatarUrl, tags[], rating, attributes, usageCount | Loading / Loaded / Hover / Skeleton | Standardized height for Masonry fallback |
| Pagination / Infinite Loader | Controls page traversal | page, pageSize, hasMore | Loading / Idle / Error / End | For Tavern / search results |
| Empty State Panel | Placeholder for no data | contextType, actions[] | Visible / Hidden | Encourages creation or refine filter |
| Confirmation Dialog | Critical action confirmation | title, body, confirmLabel | Open / Closed / Busy | Esc + backdrop dismiss |
| Progress Bar / Queue Slot | Generation / processing status | status, eta, cost, position | InQueue / Processing / Completed / Failed / Canceled | Polling or websocket updates |
| Skeleton Loaders | Placeholder while fetching | variant | Shimmer / Static | For perceived performance |
| Breadcrumbs (Optional) | Secondary navigation depth | path[] | Collapsed / Expanded | Maybe only in admin |
| Footer (Optional) | Legal, Terms, Privacy links | links[] | — | Conditionally present |

---

## 3. Screen Catalog

### Index of Screens

1. Landing / Explore
2. Sign In
3. Sign Up
4. Password Reset (Request + Confirm)
5. Roleplay Preview (Marketing / Upsell)
6. Tavern (Character Hub)
7. Character Creation Wizard
8. Character Detail Page
9. Chat / Roleplay Session
10. Image Generation (Generate)
11. Generation Queue Overlay / Panel
12. Affiliate Program Page
13. Get Gems (Credits Purchase)
14. Checkout Flow (Plan Selection + Payment)
15. Payment Success / Failure
16. User Profile (Public View)
17. Account Settings (Profile, Security, Privacy, Notifications)
18. Notifications Center (Optional Consolidated View)
19. Onboarding Flow (First-time user)
20. Downtime / System Status Banner (Global ephemeral)
21. Error Pages (404, 500, Network Offline)
22. Moderation / Report Dialogs (Embedded flows)
23. Admin / Moderation Dashboard (Internal – optional but outlined)
24. Legal Pages (Terms, Privacy, Content Policy)
25. Session Timeout / Re-auth Modal
26. Search Results (If decoupled from Tavern)
27. Rate Limit / Quota Reached Overlay
28. Referral / Invitation Landing
29. Gems Balance History / Transactions
30. Audit Log (User-facing security history)

Each screen below includes: Purpose, Primary Users, Core Actions, Layout, Component Breakdown, Data Contracts, States, Edge Cases, Analytics, Accessibility (a11y), Security/Privacy, Performance & Technical Notes, Open Questions.

---
### 3.1 Landing / Explore
Purpose: Initial impression; highlight trending characters & prompts; funnel users to sign up, Tavern, Generate, or Discord.
Primary Users: New visitors, returning casual users.
Core Actions: Browse curated sets (Fast Load, Popular, New); click character; sign up; open generation; join Discord; promotional claim for free gems.
Layout:

- Hero Banner (Optional) or Promo Strip (Free Gems CTA)
- Category Tabs/Filters: Fast Load | Popular | New
- Character Grid (Paginated or infinite)
- Discord CTA Panel
- Footer (optional)
Components: Top Nav, Promo Banner, Tabs, Character Cards, Grid Loader, CTA Buttons, Toasts.
Data Contracts:
- GET /api/characters?sort=popular&limit=... -> { items: CharacterSummary[], nextCursor }
- CharacterSummary: { id, name, avatarUrl, shortDescription, tags[], ratingAvg, ratingCount, gemCostPerMessage?, nsfwFlags, lastActive }
States: Loading (skeleton cards), Empty (if no characters), Error (retry), Partial load for infinite.
Edge Cases: API timeout fallback; no trending dataset; user blocked from NSFW (region/age gating) => sanitized set.
Analytics: page_view.explore, click.character_card(id), tab_switch(category), cta.discord, cta.signup, impression.promo_banner.
Accessibility: Tabable cards; ARIA labels for categories; high contrast focus rings; alt text for avatars (character name).
Security/Privacy: Avoid exposing sensitive moderation flags; ensure safe filtering; sanitize promotional user-generated text.
Performance: Pre-fetch first 2 categories in parallel; use responsive image sizes (srcset); skeletons < 60ms mount; cache list in memory.
Open Questions: Do we geofence mature content? Are anonymous chat previews allowed?

### 3.2 Sign In
Purpose: Authenticate returning users.
Primary Users: Registered users.
Core Actions: Enter email/username + password; alternative social logins; forgot password.
Layout: Form card centered, optional side panel with artwork.
Components: InputEmail, InputPassword (show/hide), SocialLoginButtons[], RememberMe checkbox, Submit, Forgot link.
Data Contracts:

- POST /api/auth/login { identifier, password } -> { token, refreshToken, user, gemBalance }
- Errors: { code: INVALID_CREDENTIALS | LOCKED | RATE_LIMIT, message }
States: Idle, Submitting (disabled), Error (inline), Rate limited (cooldown countdown).
Edge Cases: Account banned => show contact support; Email not verified => resend verification modal.
Analytics: auth.login_attempt, auth.login_success, auth.login_failure(code), auth.social_click(provider).
Accessibility: Proper label association; enter key submit; error text ARIA-live polite.
Security: Rate limit by IP + account; lock after N attempts; store tokens HttpOnly; enforce TLS; disallow detailed error leakage.
Performance: Lightweight page (<50 KB JS); defer non-critical analytics until post-auth.
Open Questions: Support WebAuthn? 2FA optional?

### 3.3 Sign Up
Purpose: Register new users.
Primary Users: Visitors.
Core Actions: Provide email, username, password, age confirmation, accept terms.
Layout: Similar to Sign In; optionally marketing bullet list.
Data:

- POST /api/auth/register { email, username, password, birthYear, agreeTerms } -> { user, token, requiresEmailVerification }
Validation: Unique username; profanity filter; password strength.
States: Idle, Validating (async username check), Submitting, Email verification pending.
Edge Cases: Disposable email detection; Underage rejection; duplicate.
Analytics: auth.signup_start, auth.signup_success, auth.signup_fail(reason), auth.username_check.
Accessibility: Password requirements listed with semantic list; error hints updated live.
Security: Hash passwords (Argon2id), strong rate limiting, captcha after suspicious traffic, email verification before sensitive actions.
Performance: Debounced username availability check.
Open Questions: Referral code input? Affiliate auto-linking?

### 3.4 Password Reset (Request + Confirm)
Purpose: Recovery flows.
Data:

- POST /api/auth/password-reset/request { email }
- POST /api/auth/password-reset/confirm { token, newPassword }
Edge Cases: Token expired/invalidate all; share identical success response (no user enumeration).
Security: Signed short-lived token; rotating token invalidation; password strength enforced.
Analytics: password_reset_request, password_reset_complete.

### 3.5 Roleplay Preview
Purpose: Marketing/teaser for roleplay UI; encourage sign-in.
Content: Screenshot mock, feature bullets (immersive chat, dynamic personality), limited sample lines (static, non-AI).
Actions: Sign Up, Try Demo (limited), Learn more.
Edge Cases: Demo exhaustion (daily limit), mobile adaptation.
Analytics: preview.view, preview.cta_signup, preview.demo_start.
Security: Ensure no real AI usage for anonymous demo if cost risk.

### 3.6 Tavern (Character Hub)
Purpose: Discovery & management of characters (browse, search, create).
Layout Sections:

- Header: Title "Tavern" with beta badge.
- Action Bar: Create Character button (+), link to external guide (Notion), search input, sort dropdown, filters (Tags, NSFW toggle, Popular/New/Trending/Recent/Fast Load).
- Tab Row: Fast Load | Popular | Trending | New | Recent
- Character Grid
- Pagination / Infinite Loader
Components: SearchBox (with clear), TagFilterPanel (collapsible), SortSelect, CharacterCard (with metrics), GuideLink.
Data Contracts:
- GET /api/characters?filter=...&sort=...&q=... -> list
- GET /api/tags -> { tags[] }
- Character metrics precomputed (popularityScore, trendingScore).
States: Loading initial; Filtering (dim content + shimmer); Empty (no results -> refine prompt); Error.
Edge Cases: Excessive tag selection (limit 10); Query too broad (throttle suggestions); Mis-tagged NSFW flagged for moderation.
Analytics: tavern.view, tavern.filter_apply, tavern.search(queryLength), tavern.character_click(id), tavern.create_character_click.
Accessibility: Search labeled; tags aria-pressed; infinite scroll announces new items.
Security: Filter out banned characters (soft-delete flag); prevent injection via tag names.
Performance: Use windowing (react-window) for large grids; pre-warm next page request; compress JSON.
Open Questions: Should users star/favorite characters? Sorting by rating/time alive?

### 3.7 Character Creation Wizard
Purpose: Let users author a new persona.
Steps (multi-step modal or page):

1. Basics: Name, Short Description, Long Bio.
2. Personality & Behavior: Traits[], Example dialogues[], Style presets.
3. Visuals: Avatar upload (cropper), Gallery images.
4. Tags & Classification: Tag selection (auto-suggest), NSFW level, Allowed content toggles.
5. Monetization / Visibility: Public/Private, publish now/later, optional premium flag.
6. Review & Submit.
Components: Stepper, Form fields, TagAutoComplete, ImageUploader (client compression), Example Dialogue Editor (list of pairs), Preview Panel.
Data Contracts:

- POST /api/characters -> { id }
- PATCH /api/characters/:id/steps
- Media upload via signed URLs.
Validation: Name uniqueness (scoped), length constraints, blocked words.
States: Draft (autosave), Publishing (spinner), Success (redirect), Validation errors per step.
Edge Cases: Loss of connection mid-upload; unsaved changes warning; exceeding tag limit; image moderation fail.
Analytics: character_create.start, character_create.step_view(step), character_create.submit, character_create.validation_error(field).
Accessibility: Step headings h2; avatar uploader with keyboard cropping handles; error summary at top.
Security: Sanitize HTML in bios (strip scripts); virus scan images; content classification scanning.
Performance: Debounced autosave; chunked uploads; optimistic step navigation.
Open Questions: Approval workflow before public listing?

### 3.8 Character Detail Page
Purpose: Deep view; entry point to start chat; showcase persona.
Sections:
- Header: Name, avatar, tags, rating, create chat button.
- Bio & Personality Traits.
- Example Conversations (expandable list).
- Gallery (lightbox modal).
- Statistics: CreatedAt, usageCount, favorites (if implemented).
- Report / Block buttons (menu).
Data:
- GET /api/characters/:id -> CharacterFull
CharacterFull: fields + extended biography, author info (limited), moderationStatus.
Actions: Start Chat -> create session; Favorite (toggle); Report; Share link.
States: Loading skeleton; Error (not found / removed); Private (access denied).
Edge Cases: Character unpublished; Author banned; Gallery empty -> placeholder.
Analytics: character.view(id), character.start_chat, character.favorite_toggle, character.report_click.
Accessibility: Avatar alt; keyboard lightbox; headings structured.
Security: Hide internal moderation notes; restrict private characters by permission.
Performance: Lazy-load gallery images; pre-fetch chat bootstrap on hover of Start Chat.

### 3.9 Chat / Roleplay Session
Purpose: Real-time AI conversation with selected character.
Layout:
- Chat Header: Character avatar/name, session menu (Rename session, Export, Delete, Settings), gem balance, end session?
- Message Stream: User + AI messages, system notices (credit deductions, warnings), time stamps.
- Input Composer: Text area (autosize), send button, quick action chips (preset prompts), token/gem cost preview.
- Side Panel (optional collapsible): Character profile summary, memory/notes, conversation settings (temperature, style), session stats.
Components: VirtualizedMessageList, MessageBubble, TypingIndicator, RegenerateButton (on last AI message), RateFeedback (thumbs / star), TokenUsageBadge.
Data Contracts:
- POST /api/chat/sessions { characterId } -> { sessionId }
- POST /api/chat/sessions/:id/message { content } -> streaming SSE / WebSocket message events.
- Event Types: token_delta, message_complete, error, moderation_block, credit_update.
- POST /api/chat/sessions/:id/rate { messageId, rating }
States: Idle (no messages), Streaming (AI responding), Awaiting user, Paused (insufficient gems), Error (network), Reconnecting.
Edge Cases: Connection drop (auto-retry with backoff); gem depletion mid-generation -> partial cut + upsell modal; moderation block (flag explanation); user attempts rapid-fire sending -> rate limit toast.
Analytics: chat.session_start, chat.message_send(length), chat.message_receive(tokens), chat.regenerate, chat.rating_submit, chat.gem_insufficient.
Accessibility: Live region for new AI messages; keyboard shortcuts (Ctrl+Enter send); semantic list for messages; focus management when streaming.
Security: Strip prompt injection artifacts; content filter pre-send and pre-display; enforce per-user rate limit; redact banned terms in output if required.
Performance: Stream tokens incrementally; recycle DOM nodes (windowing > 200 messages); compression over WS if large metadata; diff-based memory updates.
Open Questions: Memory persistence strategy? Per-session vs global memory fragments.

### 3.10 Image Generation (Generate)
Purpose: Create images with optional character context, pose presets, style and quality choices.
Sections (from captured page):
- Select Character (current selection box – clickable to open character chooser modal with search)
- Prompt Input (multiline, with token/length guidance, negative prompt optional?)
- Pose Presets Grid (Doggy, Cowgirl, Reverse, etc.) – selecting inserts/augments prompt.
- Number of Images Selector (1 | 4 | 9) – radio or segmented control.
- Image Orientation (Portrait | Square)
- Style (Default | Cartoon ... extendable)
- Generation Quality (Quick Draft, Fast, Balanced, High Quality, Ultra) with speed icons ⚡ / clocks.
- Generate Button (cost indicator e.g., shows required gems; disabled when insufficient).
- Queue / Result Panel (shows generation progress, thumbnails when done; clicking opens lightbox with metadata + download + report).
Data Contracts:
- POST /api/generate { characterId?, prompt, posePreset?, count, orientation, style, quality } -> { jobId, estimatedCost, estimatedTime }
- GET /api/generate/jobs/:id -> { status, progress, images[], failureReason }
- WebSocket/SSE: job_update events.
- Image Object: { id, url, thumbUrl, seed, promptFinal, safetyScores, size, generatedAt }
States: Idle, Submitting (Validating), Queued (position), Processing (progress bar / spinner), Completed (grid), Partial Failure (some images failed), Failed (error message + retry option).
Edge Cases: Exceeds daily limit; prompt flagged by moderation; server downtime banner (as seen); orientation mismatch fallback; pose preset injection duplicates adjectives; user closes tab mid-generation (background continue + notification on return).
Analytics: gen.open, gen.start(quality,count), gen.complete(images,count), gen.fail(reason), gen.pose_select(name), gen.style_select(name), gen.quality_select(tier).
Accessibility: Pose presets have ARIA role=button + visually hidden description; progress announced politely; thumbnails have alt text derived from final prompt (truncated).
Security: Sanitize prompt (remove personally identifiable info if policy); block disallowed content; job isolation per user; revalidate gem balance server-side.
Performance: Client-side prompt trimming; optimistic UI for queue position; batch image requests; CDN caching with signed URLs; placeholder blur-up.
Open Questions: Negative prompts? Seed control? Variation generation?

### 3.11 Generation Queue Overlay / Panel
Purpose: Show active + recent generation tasks.
Data: GET /api/generate/jobs?status=incomplete -> { jobs[] }
States: Collapsed icon with badge; expanded list; empty; error.
Actions: Cancel job, View result, Retry failed.
Analytics: queue.view, queue.cancel(jobId), queue.retry(jobId).
Performance: Poll 3–5s or use WS; limit history (last 20).

### 3.12 Affiliate Program Page
Purpose: Recruit affiliates; show commission structure (15%); provide referral link & stats (if logged in).
Sections: Hero (reward pitch), Commission Explainer, How It Works Steps, Dashboard (if authed), FAQ, Terms link.
Data:
- GET /api/affiliates/me -> { referralCode, clicks, signups, purchases, commissionPending, commissionPaid }
- POST /api/affiliates/request (if gating) -> { status }
Actions: Copy link, Apply (if not active), Withdraw commission (if threshold reached), Share social.
Edge Cases: Downtime notice (like sample); insufficient balance to withdraw; banned affiliate.
Analytics: affiliate.view, affiliate.copy_link, affiliate.withdraw_request(amount), affiliate.apply.
Security: Prevent forging referral codes; server-side attribution (cookie + last click window); anti-fraud checks (IP clustering).
Performance: Cache stats; incremental number animations.

### 3.13 Get Gems (Credits Purchase)
Purpose: Display gem packs & pricing; upsell special deals; show current balance.
Sections: Balance Summary, Gem Packs Grid (each: amount, price, bonus%), Promo code input, Payment methods row, FAQ.
Data:
- GET /api/gems/packs -> { packs[] }
Pack: { id, amount, price, currency, bonusPercent, isBestValue, isPopular }
- POST /api/gems/checkout { packId, paymentProvider } -> { checkoutSessionUrl }
Edge Cases: Pricing mismatch; currency detection; user in restricted region.
Analytics: gems.view, gems.pack_click(id), gems.checkout_start(provider), gems.promo_apply(code, success).
Security: Validate price server-side; tamper-proof pack IDs; store transactions immutably.
Performance: Preload provider SDK (lazy); skeleton for packs.

### 3.14 Checkout Flow (Selection + Payment)
Purpose: Handle payment provider redirection / embedded purchase.
States: Pending provider redirect; Payment in progress; Completed; Failed.
Edge Cases: User cancels provider; double submission; webhooks delayed.
Security: Webhook signature validation; idempotent order creation.
Analytics: checkout.session_created, checkout.payment_success, checkout.payment_failure(code).

### 3.15 Payment Success / Failure
Purpose: Resolve purchase; show updated balance / retry guidance.
Actions: Return to previous context (chat, generation, gems page), Start first generation (upsell), share referral.
Analytics: checkout.success_screen_view, checkout.failure_screen_view.

### 3.16 User Profile (Public View)
Purpose: Display limited public info + authored characters.
Sections: Avatar, Username, Bio, Stats (joined date, charactersCount, favorites?), Character grid, Report user.
Data: GET /api/users/:username/public
Edge Cases: Private profile; banned user placeholder.
Analytics: profile.view(userId).
Security: Redact email; enforce content policy on bio.

### 3.17 Account Settings
Sub-Tabs:
1. Profile (avatar upload, display name, bio)
2. Security (password change, 2FA setup, session management list, revoke tokens)
3. Privacy (NSFW visibility preferences, block list, data export request)
4. Notifications (email toggles, Discord integration, push opt-in)
5. Billing & Gems History (transaction list, invoices download, commissions)
Components: TabNav, Form groups, Danger Zone (delete account).
Data:
- GET /api/me
- PATCH /api/me/profile
- GET /api/me/sessions -> { sessions[] }
- DELETE /api/me/sessions/:id
Edge Cases: Avatar moderation fail; 2FA reset; export request rate-limited.
Analytics: settings.view(tab), settings.profile_save, settings.security_session_revoke.
Security: Re-auth before sensitive changes; CSRF protection on forms; audit log entries.

### 3.18 Notifications Center
Purpose: Central hub (optional) consolidating system, affiliate, generation completions.
Data: GET /api/notifications?cursor=...
Notification: { id, type, title, body, createdAt, read, actionUrl }
Actions: Mark read (single / all), Navigate.
Edge Cases: Large backlog -> pagination; real-time push.
Analytics: notifications.view, notifications.click(id), notifications.mark_all_read.

### 3.19 Onboarding Flow
Purpose: Guide first-time user to create / pick character & generate first chat or image.
Steps: Welcome -> Choose interest tags -> Suggest characters -> Start first chat OR Generate image -> Show gem usage tips.
Data: POST /api/onboarding/complete
Analytics: onboarding.start, onboarding.step(step), onboarding.complete.
Performance: Pre-fetch curated recommendations.

### 3.20 Downtime / System Status Banner
Purpose: Communicate degraded service (as seen: "We're facing a downtime...").
Data: GET /api/status -> { incidents[], degradedServices[] }
Placement: Top global; dismissible (localStorage store); severity color-coded.
Analytics: status_banner.view(incidentId), status_banner.dismiss.

### 3.21 Error Pages (404 / 500 / Offline)
Purpose: Clear messaging + recovery actions.
Edge Cases: Service worker offline detection triggers offline page; broken deep link.
Analytics: error.404(path), error.500(traceId), error.offline.

### 3.22 Moderation / Report Dialogs
Purpose: Allow users to flag content.
Report Types: Character, Message, Image, User.
Data: POST /api/report { targetType, targetId, reasonCode, details }
Feedback: Thank you message; rate limit 1/min per target.
Security: Spam detection; store reporter hashed IP.
Analytics: report.submit(type, reasonCode).

### 3.23 Admin / Moderation Dashboard (Internal)
Purpose: Internal controls (not user-facing but needed for full parity architecture).
Features: Queue of reports, Character approval, User bans, Content re-generation, Stats monitors.
Components: Data tables with filters, Bulk action toolbar, Detail drawer.
Security: Role-based access (RBAC), audit logging, IP allowlist.
Analytics: admin.report_resolved, admin.character_action(actionType).

### 3.24 Legal Pages
Static markdown served: Terms, Privacy, Content Policy, Affiliate Terms.
SEO-friendly, cached aggressively.

### 3.25 Session Timeout / Re-auth Modal
Triggered after inactivity or privileged action.
Analytics: auth.reauth_prompt, auth.reauth_success.

### 3.26 Search Results (Dedicated)
If separated from Tavern: supports multi-entity search (characters, users, images?).
Query suggestions, highlight terms.

### 3.27 Rate Limit / Quota Reached Overlay
Shows when user exceeds chat or generation cap.
Actions: Upgrade (buy gems), Wait timer, Contact support.
Analytics: quota.hit(context), quota.upgrade_click.

### 3.28 Referral / Invitation Landing
If visiting ?ref=CODE, show referral attribution card, bonus gem offer, expedited sign-up callout.
Analytics: referral.landing(code).

### 3.29 Gems Balance History / Transactions
Table: Date, Action (Purchase / Generation / Chat / Bonus / Affiliate Commission), Delta, Balance After, ReferenceId.
Data: GET /api/gems/ledger?cursor=...
Analytics: gems.ledger_view.
Security: Immutable ledger (append-only).

### 3.30 Audit Log (User Security History)
List of sign-ins (device, IP general region), password changes, 2FA events.
User empowerment & trust.
Analytics: audit.view.

---
## 4. Data Model (High-Level)

Entities (selected):
- User: { id, username, email (hashed view), avatarUrl, bio, roles[], gemBalance, referralCode, settings, flags }
- Character: { id, ownerId, name, shortDesc, longBio, traits[], exampleDialogues[], avatarImageId, galleryImageIds[], tags[], nsfwLevel, visibility, stats, moderation: { status, reasons[] } }
- ChatSession: { id, userId, characterId, createdAt, messages[], state, gemSpent, settingsOverrides }
- ChatMessage: { id, sessionId, role(user|ai|system), content, tokensUsed, gemCost, createdAt, moderationFlags[] }
- GenerationJob: { id, userId, characterId?, promptRaw, promptFinal, posePreset, style, qualityTier, countRequested, status, progress, images[], gemCostTotal, createdAt }
- GeneratedImage: { id, jobId, url, metadata(seed, orientation, style, quality), safetyScores, moderationStatus }
- GemTransaction: { id, userId, type, amountDelta, balanceAfter, referenceType, referenceId, createdAt }
- AffiliateAccount: { userId, code, clicks, attributedSignups, commissionPending, commissionPaid, status }
- Notification: { id, userId, type, payload, readAt }
- Report: { id, reporterId, targetType, targetId, reasonCode, details, status }

---
## 5. Cross-Cutting Concerns

### 5.1 Authentication & Authorization
- JWT or session token (HttpOnly cookie) + refresh rotation.
- Role sets: user, affiliate, moderator, admin.
- Actions requiring elevated role: content removal, user suspension, ledger adjustments.
- 2FA: TOTP optional; enforced for moderators.

### 5.2 Gems Economy Rules
- Chat message cost: dynamic by token count or flat per AI response tier.
- Image generation cost: base cost * quality multiplier * count.
- Insufficient gem check server-side always; client predictive estimate.
- Refund policy for failed image jobs (automatic partial refunds for failed outputs).

### 5.3 Moderation
- Pre-generation prompt scanning.
- Post-generation AI output & image scanning (async; if violation -> retroactive removal + notice + refund logic).
- User report triage queue sorted by severity + recency.

### 5.4 Observability
- Structured event bus (analytics events -> queue -> warehouse).
- Performance metrics: TTFB, LCP, CLS, Chat streaming latency (p50/p90), Generation queue wait time.
- Error tracking: Sentry style with trace IDs in 500 pages.

### 5.5 Internationalization (Future)
- English default; architecture prepared for locale bundles for static strings.

### 5.6 Accessibility Strategy
- WCAG 2.1 AA target.
- Color contrast validated for CTAs.
- Keyboard nav priority: Chat input -> message list -> side panel -> settings.
- Live regions for streaming tokens and queue updates.

### 5.7 Security & Privacy
- Input sanitation for all user-submitted text.
- CSP: default-src 'self'; strict media domains for CDN.
- Rate limiting layers: IP + User + Action category.
- Logging: Avoid storing raw prompts containing personal data (hash or redact heuristics).
- Account deletion: soft-delete + delayed purge window.

### 5.8 Performance Principles
- Code splitting by route (explore, tavern, generate, chat heavy bundle separated).
- Edge caching for public character lists.
- WebSocket multiplex for chat + job updates.
- Client memory thresholds: prune chat older than N messages (with on-demand fetch for history).

### 5.9 Analytics Event Naming Conventions
- namespace.action_detail (snake)
- Required fields: userId (if authenticated), sessionId (device), timestamp, screen, referrer.
- PII avoidance — no raw email/username.

### 5.10 Error Handling UX
- Soft errors (retryable) use inline banners.
- Hard errors escalate to modal or dedicated screen.
- Provide traceId for support.

---
## 6. Screen-Level Edge Case Matrix (Selected Highlights)

| Screen | Edge Case | Handling Strategy |
|--------|-----------|-------------------|
| Chat | Network drop mid-stream | Show reconnect toast; attempt silent resume; fallback to manual retry button |
| Chat | Double send (rapid fire) | Disable send until last message accepted; queue local draft |
| Generate | Job fails partially | Show per-image failure icon; offer regenerate only failed subset |
| Generate | User closes tab | Continue processing; store completion -> notification / badge on return |
| Tavern | Tag explosion (>100 tags) | Virtual scroll list with search filter; limit selection count |
| Character Create | Loss of connectivity | Local draft persistence in IndexedDB; sync when online |
| Checkout | Webhook delay | Pending state with polling; allow user to manually refresh order |
| Affiliate | Fraud detection | Freeze payouts; surface neutral status message; escalate internally |
| Gems Ledger | Large history | Cursor pagination; jump to top button |

---
## 7. Open Questions & Assumptions

| Area | Assumption | Risk | Proposed Validation |
|------|------------|------|---------------------|
| Chat cost model | Flat per message + quality multiplier | Mispricing -> margin loss | A/B test dynamic vs flat |
| Image negative prompts | Not initially exposed | User dissatisfaction | Add optional advanced panel iteration 2 |
| Character approval | Auto-publish w/ retro moderation | Policy breach risk | Add fast ML pre-check stage |
| Referral tracking window | 30 days cookie | Attribution disputes | Make configurable + transparent |
| 2FA adoption | Optional | Account takeover risk | Incentivize with bonus gems |

---
## 8. Analytics Event Inventory (Non-Exhaustive)

- explore.page_view
- tavern.view / tavern.filter_apply / tavern.search
- character.view / character.start_chat / character.favorite_toggle
- chat.session_start / chat.message_send / chat.message_receive / chat.regenerate / chat.rating_submit
- gen.open / gen.start / gen.complete / gen.fail
- gems.view / gems.pack_click / gems.checkout_start / checkout.payment_success / checkout.payment_failure
- affiliate.view / affiliate.copy_link / affiliate.withdraw_request
- auth.signup_start / auth.signup_success / auth.login_success / auth.login_failure
- report.submit
- quota.hit
- onboarding.start / onboarding.complete

---
## 9. Privacy & Compliance Considerations

- Age gating for explicit NSFW access (self-attested min age + disclaimers).
- Data minimization: Do not store full raw chat long-term unless user exports; keep truncated context windows.
- GDPR/CCPA: Export + deletion endpoints; record consent timestamps.
- Moderation transparency: Provide user with generic reasons, avoid disclosing classifier specifics.

---
## 10. Implementation Priorities (Suggested Phases)

Phase 1 (MVP): Auth, Explore, Tavern, Character Creation basic, Chat (streaming), Gems purchase (single provider), Image Generation basic (single quality), Affiliate simple, Moderation minimal (manual), Basic analytics.
Phase 2: Quality tiers, Queue overlay, Advanced prompts, Multi-step creation wizard polish, Ledger, Notifications, Reports workflow.
Phase 3: Affiliate dashboard enhancements, A/B experimentation layer, 2FA, Advanced moderation automation, Audit log.
Phase 4: Localization, Performance deep optimization, Advanced personalization, Mobile PWA, Real-time presence.

---
## 11. Acceptance Criteria Summary (Sampling)

- Chat message send < 150ms request ACK p50.
- Image generation queue latency displayed (<5s accuracy of ETA).
- Character creation autosave every 5s or on field blur without data loss after refresh.
- All interactive elements keyboard navigable, no focus traps.
- Gem balance never negative; ledger deltas reconcilable sum to balance.
- Reports acknowledged with response id.

---
## 12. Future Extensibility Hooks

- Plugin architecture for custom character behavior modules.
- Multi-model selection (OpenAI vs local) per conversation.
- Marketplace for premium characters (rev share with creators).
- Webhooks for affiliate conversions.
- Web push notifications for generation completion.

---
## 13. Appendix: Glossary

| Term | Definition |
|------|------------|
| Gems | Virtual currency used for AI operations (chat tokens, image generation). |
| Fast Load | Likely characters with low initialization overhead or cached embeddings. |
| Trending | Character usage velocity-based ranking. |
| Quality Tier | Preset controlling model inference cost/time for images. |
| Pose Preset | Predefined textual prompt fragment modifying composition. |
| Moderation Block | System preventing content display due to policy match. |
| Session Memory | Summarized history influencing future AI responses. |

---
## 14. Outstanding Items To Clarify Later

1. Specific moderation provider(s) & thresholds.
2. Terms for revenue share vs fixed affiliate percentage (currently 15%).
3. Rate limit tiers (anonymous vs authenticated vs premium?).
4. Multi-currency pricing or USD only.
5. Support for bulk image download zip.

---
End of specification.
