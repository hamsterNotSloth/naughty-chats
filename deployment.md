# Deployment Plan: Naughty Chats (FastAPI + Next.js) – Azure (Container Apps + Cosmos DB NoSQL)

## 1. Objectives

Deploy FastAPI API + Next.js frontend to Azure using:

- Azure Container Apps (ACA) for both frontend (SSR) and backend
- Azure Container Registry (ACR) for image storage
- Azure Cosmos DB (Core API / NoSQL) for persistence (users, characters)
- Entra ID for auth (authoritative)
- Log Analytics for logs (App Insights + tracing later)

Phase 1: Manual CLI provisioning (COMPLETED – backend & frontend live, healthy revision deployed).
Phase 2: Infrastructure as Code (Bicep + azd) + CI/CD.
Pivot: Original PostgreSQL design fully removed. Cosmos DB adopted for speed & flexibility.

## 2. Current State Summary

| Aspect | Status |
|--------|--------|
| Backend | FastAPI async, Uvicorn (workers=2), port 8000 |
| Frontend | Next.js 15 App Router, port 3000 |
| Data Layer | Cosmos DB (containers: users, characters) |
| Auth | Entra ID (OIDC access tokens) |
| Seeding | (Updated) No automatic seeding; manual script `backend/seed_characters.py` |
| CORS | Controlled via ALLOWED_ORIGINS env |
| Observability | Log Analytics only (no tracing yet; probes pending) |
| Deployment Script | Creates ACR, CAE, Cosmos, container apps |

## 3. Target Azure Architecture

| Layer | Service | Purpose | Notes |
|-------|---------|---------|-------|
| Frontend | ACA (Node 20) | SSR + static assets | Could later move to Static Web Apps |
| Backend API | ACA (Python 3.11) | FastAPI microservice | Autoscale via KEDA |
| Images | ACR | Container image registry | Tag with git SHA + digest |
| Database | Cosmos DB (Core) | JSON docs for users/characters | Partition key `/id` (current) |
| Identity | Entra ID | OAuth2/OIDC tokens | Enforce after Phase 1 |
| Secrets | ACA secrets (Phase 1) | Cosmos key (temporary) | Migrate to Key Vault + MI |
| Logging | Log Analytics | Centralized logs | App Insights later |
| (Future) Queue | Service Bus/Event Grid | Async workflows | Deferred |
| (Future) Cache | Azure Cache for Redis | Hot read caching | Deferred |

### 3.1 Data Model (Current Document Shapes)

users:

```json
{
  "id": "<uuid>",
  "email": "user@example.com",
  "username": "player1",
  "hashed_password": "...",
  "gem_balance": 0,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

characters:

```json
{
  "id": "<uuid>",
  "name": "Nova",
  "avatar_url": "https://...",
  "short_description": "...",
  "tags": ["ai","space"],
  "rating_avg": 4.7,
  "rating_count": 120,
  "gem_cost_per_message": 3,
  "nsfw_flags": false,
  "last_active": "2024-01-01T00:00:00Z"
}
```

### 3.2 Access Pattern & Partitioning

- Simple point lookups (user by username/email) — use application-level uniqueness.
- Character listing — paginate & later refine RU (add composite indexes post profiling).
- Partition key currently `/id` for simplicity; revisit for hot partitions if scale triggers.

### 3.3 Security Evolution

Local JWT fallback has been fully removed. All authenticated calls require a valid Entra ID access token. Next phase focuses on moving secrets into Key Vault and enabling Cosmos DB RBAC via Managed Identity.

| Phase | Secrets | Cosmos Auth | Network | Auth |
|-------|---------|------------|---------|------|
| Current | ACA secrets (minimal) | Primary key | Public endpoint | Entra tokens |
| Next | Key Vault + MI | AAD RBAC | Private Endpoint/VNet | Entra tokens |

## 4. Resource Naming (prefix: `nchat`, env: `dev`)

| Resource | Example |
|----------|---------|
| Resource Group | rg-nchat-dev |
| Container Apps Env | cae-nchat-dev |
| ACR | acrnchatdev |
| Backend Container App | ca-nchat-api-dev |
| Frontend Container App | ca-nchat-web-dev |
| Cosmos Account | cosmos-nchat-dev |
| Cosmos Database | nchatsdb |
| (Later) Key Vault | kv-nchat-dev |
| Log Analytics | law-nchat-dev |
| App Insights (later) | appi-nchat-dev |

## 5. Environment Variables

Backend (authoritative list):

- ALLOWED_ORIGINS
- COSMOS_ENDPOINT
- COSMOS_KEY (to be replaced by RBAC)
- COSMOS_DATABASE (default `nchatsdb`)
- COSMOS_USERS_CONTAINER (default `users`)
- COSMOS_CHARACTERS_CONTAINER (default `characters`)
- COSMOS_AUTO_PROVISION (false in cloud)
- ENTRA_TENANT_ID
- ENTRA_API_AUDIENCE (Application ID URI e.g. `api://API_APP_ID` or bare client ID)
- ENTRA_JWKS_URL (optional override; normally derived)

Removed legacy variables: `SECRET_KEY`, `LOCAL_AUTH_ENABLED`.

Frontend:

- NEXT_PUBLIC_API_BASE_URL
- NEXT_PUBLIC_ENTRA_CLIENT_ID / NEXT_PUBLIC_ENTRA_TENANT_ID / NEXT_PUBLIC_ENTRA_API_SCOPE

## 6. Completed Changes (Phase 1 Wrap)

- Removed PostgreSQL stack (ORM, migrations, DSN)
- Added `cosmos.py` with client + CRUD + health + seeding
- Updated `main.py` to use Cosmos via thread offload
- Added fail-fast startup (missing secrets / unhealthy Cosmos)
-- Deployment script provisions Cosmos + containers
- Switched backend container CMD to Uvicorn (removed unused gunicorn path)
- Added email-validator dependency (Pydantic EmailStr)
- Healthy backend revision deployed (api-nchat-dev--0000003)

## 7. Pending Changes (Phase 2+)

| Item | Rationale |
|------|-----------|
| Real IDs in API responses | Frontend contract & linking |
| Entra token validation | Remove local JWT in cloud |
| Managed Identity + Key Vault | Eliminate static keys |
| Structured logging & tracing | Ops & debugging (OpenTelemetry + App Insights) |
| Pagination & indexing | RU optimization |
| CI/CD (GitHub Actions + azd) | Repeatable deployments |
| App Insights + OpenTelemetry | Distributed telemetry |

## 8. Manual Deployment (CLI Sequence)

### 8.0 Entra ID (Azure AD) App Registrations (One-time per tenant / environment)

You must create two App Registrations: one for the API (exposes a scope) and one for the SPA (frontend) that requests that scope. Replace placeholders (ORG, ENV, TENANT_ID, etc.). You need Azure AD (Entra ID) permissions to create and consent.

```bash
# Names & identifiers
API_APP_NAME="nchat-api-dev"
SPA_APP_NAME="nchat-spa-dev"

# 1. Create API app (no implicit grant; just standard web/api)
API_APP=$(az ad app create \
  --display-name "$API_APP_NAME" \
  --sign-in-audience AzureADMyOrg \
  --query id -o tsv)

# 2. Add an Application ID URI (uses the appId GUID automatically)
API_APP_ID=$(az ad app show --id $API_APP --query appId -o tsv)
API_APP_URI="api://$API_APP_ID"
az ad app update --id $API_APP --identifier-uris $API_APP_URI

# 3. Expose scope (user_impersonation style) – replace adminConsentDescription as needed
SCOPE_ID=$(uuidgen)
az ad app update --id $API_APP --set api.oauth2PermissionScopes="[{\"adminConsentDescription\":\"Access Naughty Chats API\",\"adminConsentDisplayName\":\"Access Naughty Chats API\",\"id\":\"$SCOPE_ID\",\"isEnabled\":true,\"type\":\"User\",\"userConsentDescription\":\"Allow the application to access the API on your behalf.\",\"userConsentDisplayName\":\"Access the API\",\"value\":\"access\"}]"

# 4. Create SPA app
SPA_APP=$(az ad app create \
  --display-name "$SPA_APP_NAME" \
  --sign-in-audience AzureADMyOrg \
  --query id -o tsv)
SPA_APP_ID=$(az ad app show --id $SPA_APP --query appId -o tsv)

# 5. Configure SPA redirect URIs (local + production). Adjust domain.
az ad app update --id $SPA_APP --spa redirectUris="[ \"http://localhost:3000\", \"https://ca-nchat-web-dev.REGION.azurecontainerapps.io\" ]"

# 6. Grant SPA permission to call API scope
API_RESOURCE_ID=$(az ad app show --id $API_APP --query appId -o tsv)
az ad app permission add --id $SPA_APP --api $API_RESOURCE_ID --api-permissions $SCOPE_ID=Scope

# 7. Admin consent (requires admin)
az ad app permission admin-consent --id $SPA_APP

echo "API_APP_ID=$API_APP_ID"
echo "SPA_APP_ID=$SPA_APP_ID"
echo "API_APP_URI=$API_APP_URI"   # -> ENTRA_API_AUDIENCE
echo "Scope value: access"        # -> combine as api://API_APP_ID/.default for MSAL acquireToken
```

Environment variable mapping after registration:

- Backend `ENTRA_API_AUDIENCE` = `api://$API_APP_ID`
- Frontend `NEXT_PUBLIC_ENTRA_CLIENT_ID` = `$SPA_APP_ID`
- Frontend `NEXT_PUBLIC_ENTRA_API_SCOPE` = `api://$API_APP_ID/.default`

JWKS URL pattern (no need to set unless overriding):
`https://login.microsoftonline.com/$ENTRA_TENANT_ID/discovery/v2.0/keys`

```bash
export PREFIX=nchat; export ENV=dev; export LOCATION=eastus
export RG=rg-$PREFIX-$ENV; export ACR=acr${PREFIX}${ENV//-/}; export CAE=cae-$PREFIX-$ENV
export COSMOS=cosmos-$PREFIX-$ENV; export COSMOS_DB=nchatsdb

az group create -n $RG -l $LOCATION
az monitor log-analytics workspace create -g $RG -n law-$PREFIX-$ENV -l $LOCATION
WID=$(az monitor log-analytics workspace show -g $RG -n law-$PREFIX-$ENV --query customerId -o tsv)
WKEY=$(az monitor log-analytics workspace get-shared-keys -g $RG -n law-$PREFIX-$ENV --query primarySharedKey -o tsv)
az containerapp env create -n $CAE -g $RG -l $LOCATION --logs-workspace-id $WID --logs-workspace-key $WKEY
az acr create -g $RG -n $ACR --sku Basic

az cosmosdb create -g $RG -n $COSMOS --kind GlobalDocumentDB --locations regionName=$LOCATION failoverPriority=0 isZoneRedundant=False
az cosmosdb sql database create -g $RG -a $COSMOS -n $COSMOS_DB
az cosmosdb sql container create -g $RG -a $COSMOS -d $COSMOS_DB -n users --partition-key-path /id --throughput 400
az cosmosdb sql container create -g $RG -a $COSMOS -d $COSMOS_DB -n characters --partition-key-path /id --throughput 400

COSMOS_ENDPOINT=$(az cosmosdb show -g $RG -n $COSMOS --query documentEndpoint -o tsv)
COSMOS_KEY=$(az cosmosdb keys list -g $RG -n $COSMOS --type keys --query primaryMasterKey -o tsv)

az acr build --registry $ACR --image api:$(git rev-parse --short HEAD) -f backend/Dockerfile .
az acr build --registry $ACR --image web:$(git rev-parse --short HEAD) -f frontend/Dockerfile .
ACR_LOGIN=$(az acr show -n $ACR --query loginServer -o tsv)
ACR_USER=$(az acr credential show -n $ACR --query username -o tsv)
ACR_PASS=$(az acr credential show -n $ACR --query passwords[0].value -o tsv)
API_IMAGE=$ACR_LOGIN/api:$(git rev-parse --short HEAD)
WEB_IMAGE=$ACR_LOGIN/web:$(git rev-parse --short HEAD)

az containerapp create -n ca-$PREFIX-api-$ENV -g $RG --environment $CAE --image $API_IMAGE \
  --target-port 8000 --ingress external \
  --registry-server $ACR_LOGIN --registry-username $ACR_USER --registry-password $ACR_PASS \
  --secrets cosmos-endpoint="$COSMOS_ENDPOINT" cosmos-key="$COSMOS_KEY" \
  --env-vars COSMOS_ENDPOINT=secretref:cosmos-endpoint COSMOS_KEY=secretref:cosmos-key \
             COSMOS_DATABASE=$COSMOS_DB COSMOS_USERS_CONTAINER=users COSMOS_CHARACTERS_CONTAINER=characters \
             COSMOS_AUTO_PROVISION=false ALLOWED_ORIGINS="https://placeholder" \
             ENTRA_TENANT_ID=TENANT_ID ENTRA_API_AUDIENCE=api://API_APP_ID

API_FQDN=$(az containerapp show -g $RG -n ca-$PREFIX-api-$ENV --query properties.configuration.ingress.fqdn -o tsv)

az containerapp create -n ca-$PREFIX-web-$ENV -g $RG --environment $CAE --image $WEB_IMAGE \
  --target-port 3000 --ingress external \
  --registry-server $ACR_LOGIN --registry-username $ACR_USER --registry-password $ACR_PASS \
  --env-vars NEXT_PUBLIC_API_BASE_URL=https://$API_FQDN NEXT_PUBLIC_ENTRA_CLIENT_ID=SPA_CLIENT_ID \
             NEXT_PUBLIC_ENTRA_TENANT_ID=TENANT_ID NEXT_PUBLIC_ENTRA_API_SCOPE=api://API_APP_ID/.default

# (Optional) Update existing API container app after migration to remove legacy vars if previously set:
# az containerapp update -n ca-$PREFIX-api-$ENV -g $RG \
#   --remove-env-vars SECRET_KEY LOCAL_AUTH_ENABLED \
#   --set-env-vars ENTRA_API_AUDIENCE=api://API_APP_ID
```

## 9. Validation Checklist (Executed Phase 1)

| Step | Action | Expected |
|------|--------|----------|
| 1 | curl /healthz | 200 {"status": "ok"} |
| 2 | Frontend characters page | Seeded list visible |
| 3 | Register user | 200 + token; doc in users container |
| 4 | Login + /api/me | Returns user payload |
| 5 | /api/me no token | 401 |
| 6 | Entra token call | 200 |
| 7 | Log Analytics check | Request logs present |
| 8 | Rotate secret-key & restart | Old tokens invalid |

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Primary key leakage | Data exposure | Move to RBAC, rotate key |
| High RU consumption | Throttling / cost | Index tuning, caching |
| Placeholder IDs | Contract churn | Implement real IDs early |
| Missing auth enforcement | Security gap | (Resolved) Entra validation enforced |
| Over-broad CORS | Token leakage | Strict production origins |
| No backups | Data loss | Enable continuous backup |
| Secrets lifecycle | Rotation issues | Key Vault + MI |

## 11. Next Steps (Ordered – Updated Priorities)

1. Add readiness & liveness probes (/healthz) to backend Container App
2. Implement real ID propagation in responses (currently using username as id)
3. Introduce Key Vault + Managed Identity + Cosmos RBAC
4. Add App Insights + OpenTelemetry + structured logging (correlation IDs)
5. Author Bicep modules + azure.yaml (azd)
6. Create CI/CD (GitHub Actions) with build+scan+deploy
7. Pagination & index policy optimization (RU tests)

## 13. Manual Character Seeding (Updated Behavior)

Automatic seeding was removed to ensure the application fails fast if required data is missing. If you deploy a fresh environment you MUST seed characters manually before users can browse.

Steps:

```bash
# Activate virtualenv or ensure deps installed
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# Export necessary Cosmos vars (examples)
export COSMOS_ENDPOINT="https://cosmos-nchat-dev.documents.azure.com:443/"
export COSMOS_KEY="<primary-key>"
export COSMOS_DATABASE="nchatsdb"
export COSMOS_CHARACTERS_CONTAINER="characters"

# Run seeding script
python -m backend.seed_characters
```

Safety characteristics:

- Script is idempotent: exits early if characters already exist.
- No data is auto-created at API startup; empty container -> `/api/characters` returns HTTP 500 with an explicit message.
- Adjust or extend `SEED_DATA` in `backend/seed_characters.py` to add more initial characters.

Operational recommendation: Run this once as part of an environment bootstrap job (e.g., a GitHub Actions workflow step gated on empty container count) rather than embedding seeding in runtime code.

## 12. Environment Variable Matrix

| Scope | Name | Example | Secret | Notes |
|-------|------|---------|--------|-------|
| Backend | (Removed) SECRET_KEY | N/A | N/A | Eliminated (Entra authoritative) |
| Backend | COSMOS_ENDPOINT | <https://cosmos-nchat-dev.documents.azure.com:443/> | Yes | Primary endpoint |
| Backend | COSMOS_KEY | (base64) | Yes | Replace with RBAC |
| Backend | COSMOS_DATABASE | nchatsdb | No | Default fallback |
| Backend | COSMOS_USERS_CONTAINER | users | No |  |
| Backend | COSMOS_CHARACTERS_CONTAINER | characters | No |  |
| Backend | COSMOS_AUTO_PROVISION | false | No | Only true for local dev bootstrap |
| Backend | ALLOWED_ORIGINS | <https://app.example.com> | No | Comma separated |
| Backend | ENTRA_TENANT_ID | GUID | No | Required |
| Backend | ENTRA_API_AUDIENCE | api://API_APP_ID | No | Or bare client ID |
| Backend | ENTRA_JWKS_URL | <https://login.microsoftonline.com/TENANT_ID/discovery/v2.0/keys> | No | Optional override |
| Backend | (Removed) LOCAL_AUTH_ENABLED | N/A | N/A | Eliminated |
| Frontend | NEXT_PUBLIC_API_BASE_URL | <https://ca-nchat-api-dev.REGION.azurecontainerapps.io> | No | Public runtime |
| Frontend | NEXT_PUBLIC_ENTRA_CLIENT_ID | GUID | No | Public |
| Frontend | NEXT_PUBLIC_ENTRA_TENANT_ID | GUID | No | Public |
| Frontend | NEXT_PUBLIC_ENTRA_API_SCOPE | api://API_APP_ID/.default | No | Public |
| Backend | ENTRA_B2C_POLICY | B2C_1_SIGNUPSIGNIN | No | Required for B2C multi-provider flows |
| Backend | ENTRA_B2C_TENANT_PRIMARY_DOMAIN | yourtenant.onmicrosoft.com | No | Primary domain of External ID tenant |
| Backend | ENTRA_EXPECTED_ISSUER | <https://yourtenant.b2clogin.com/.../v2.0> | No | Optional explicit issuer override |
| Frontend | NEXT_PUBLIC_B2C_TENANT_NAME | yourtenant | No | Used to build B2C authority if not supplied directly |
| Frontend | NEXT_PUBLIC_B2C_USER_FLOW | B2C_1_SIGNUPSIGNIN | No | User flow / policy name |
| Frontend | NEXT_PUBLIC_ENTRA_AUTHORITY | Full authority URL | No | Optional explicit authority (overrides derived) |

Suggested secret names: `secret-key`, `cosmos-endpoint`, `cosmos-key`.

## 14. Entra External ID (B2C) – Email/Password + Social (Google, Twitter, Discord)

This project now supports Microsoft Entra External ID (formerly Azure AD B2C) so users can authenticate with:

- Local accounts (email/password)
- Federated Google (built‑in)
- Custom OpenID Connect providers (Twitter, Discord) – configured manually

### 14.1 Architecture Changes

Frontend no longer collects credentials. The `signin` and `signup` pages invoke `MSAL` redirect to the configured B2C user flow (policy). All identity UX (password, MFA, social account selection) occurs on the hosted page. After successful auth:

1. MSAL stores the ID/access tokens in the browser (localStorage).
2. The frontend calls `acquireTokenSilent` for the API scope (`api://API_APP_ID/.default` or a named scope).
3. The access token is sent to the backend (`/api/me`), which validates signature & issuer using dynamic JWKS (B2C discovery) and auto‑provisions the user if not present.

### 14.2 Required Additional Environment Variables

Backend:

```bash
ENTRA_B2C_POLICY=B2C_1_SIGNUPSIGNIN
ENTRA_B2C_TENANT_PRIMARY_DOMAIN=yourtenant.onmicrosoft.com
# Optional if auto-derivation insufficient (multiple policies) – overrides issuer match
ENTRA_EXPECTED_ISSUER=https://yourtenant.b2clogin.com/yourtenant.onmicrosoft.com/B2C_1_SIGNUPSIGNIN/v2.0
```

Frontend:

```bash
NEXT_PUBLIC_B2C_TENANT_NAME=yourtenant
NEXT_PUBLIC_B2C_USER_FLOW=B2C_1_SIGNUPSIGNIN
# If you prefer explicit authority (overrides derived):
NEXT_PUBLIC_ENTRA_AUTHORITY=https://yourtenant.b2clogin.com/yourtenant.onmicrosoft.com/B2C_1_SIGNUPSIGNIN/v2.0
```

Existing variables remain (client id, api scope, api base url). If `NEXT_PUBLIC_ENTRA_AUTHORITY` is set it takes precedence; otherwise authority is derived from tenant name + policy.

### 14.3 Creating the B2C User Flow

In the Entra admin center (External Identities):

1. Create a User Flow (Recommended type: Sign up and sign in). Name: `B2C_1_SIGNUPSIGNIN`.
2. Identity providers: Enable Email signup (local account) and add Google (built‑in) – requires Google client ID/secret.
3. Application claims: Include `email`, `preferred_username`, and `oid`.
4. (Optional) MFA: Enable if required for higher assurance.

### 14.4 Adding Google (Built‑in)

1. In External Identities > Identity Providers > Add provider > Google.
2. Supply Google Client ID & Client Secret (created in Google Cloud Console OAuth consent screen + credentials).
3. Save; ensure the provider is enabled inside the user flow.

### 14.5 Adding Twitter & Discord (Custom OpenID Connect)

Twitter and Discord require custom OIDC providers because they are not built‑in. Steps (portal driven):

1. Create app (Twitter Developer Portal / Discord Developer Portal) and obtain client ID & secret.
2. Note the issuer / authorization / token / userinfo endpoints:

- Discord OIDC issuer: `https://discord.com/api` (userinfo: `/oauth2/@me` – may require mapping). If pure OIDC not fully supported, consider an intermediate custom backend or broker. (Discord supports OAuth2; for OIDC profile you may map claims manually.)
- Twitter (v2) provides OAuth2; for OIDC‑style integration you may need to transform claims or use a gateway. (Native OIDC metadata may be limited.)

3. In External Identities > Identity Providers > Add custom OpenID Connect.
4. Fill metadata endpoint OR explicit endpoints; map `sub` → `oid` (or rely on `sub`), ensure `email` claim requested.
5. Enable provider in the user flow.

Limitations: Some social platforms (Twitter/Discord) may not expose full OIDC metadata; if so you must supply endpoints manually and may not receive all profile claims. Backend auto‑provision uses whatever `preferred_username` or `email` is present.

### 14.6 Token Validation Logic (Backend)

`backend/entra_auth.py` now derives issuer/JWKS automatically when B2C variables are set:

- Issuer: `https://<tenantPrefix>.b2clogin.com/<primaryDomain>/<policy>/v2.0`
- JWKS: `.../<policy>/discovery/v2.0/keys`
- Optional override: `ENTRA_EXPECTED_ISSUER` for strict matching across multiple policies.

### 14.7 MSAL Frontend Changes

`AuthProvider.tsx` constructs authority from `NEXT_PUBLIC_ENTRA_AUTHORITY` or derived `https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{policy}/v2.0`. The `signin` and `signup` pages now just call `login()` which triggers `loginRedirect` to the user flow.

### 14.8 Scopes & Audience

If you exposed a named scope (e.g., `access`) you can request it directly: `api://API_APP_ID/access`. Using `.default` aggregates all user‑consent scopes. Both are supported; ensure backend `ENTRA_API_AUDIENCE` matches the chosen Application ID URI root.

### 14.9 Local Development Notes

For local dev with B2C:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENTRA_CLIENT_ID=<SPA_CLIENT_ID>
NEXT_PUBLIC_ENTRA_API_SCOPE=api://<API_APP_ID>/.default
NEXT_PUBLIC_B2C_TENANT_NAME=<tenantPrefix>
NEXT_PUBLIC_B2C_USER_FLOW=B2C_1_SIGNUPSIGNIN
ENTRA_B2C_TENANT_PRIMARY_DOMAIN=<tenantPrefix>.onmicrosoft.com
ENTRA_B2C_POLICY=B2C_1_SIGNUPSIGNIN
ENTRA_API_AUDIENCE=api://<API_APP_ID>
```

### 14.10 Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 401 from /api/me | Wrong audience or issuer mismatch | Verify `ENTRA_API_AUDIENCE` and issuer derived matches token `iss` |
| acquireTokenSilent fails | Missing authority or no active account | Ensure tenant/policy env vars and initial redirect success |
| Social provider not listed | Not enabled in user flow | Re-open user flow > Identity providers > check provider |
| Invalid signature | JWKS URL mismatch or stale keys | Confirm policy name; restart backend to clear cache |

### 14.11 Future Hardening

Future improvements:

- Add multiple policies (password reset, profile edit) with per-route login hints.
- Enforce token version & `tid`/`iss` allow‑list.
- Cache user claims for display (avoid extra network calls).
- Add incremental consent or separate scopes for privileged operations.


## 15. Infrastructure as Code (azd + Bicep)

Phase 2 introduces `infra/main.bicep` and `azure.yaml` enabling fully repeatable provisioning with Azure Developer CLI (azd).

### 15.1 Bicep Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| prefix | Naming seed for resources | nchat |
| environment | Deployment stage | dev |
| location | Azure region (defaults to RG location) | eastus |
| acrName | Global unique ACR name (no dashes) | acrnchatdev |
| cosmosAccountName | (Override) Cosmos account name | cosmos-nchat-dev |
| cosmosDbName | Cosmos database logical name | nchatsdb |
| usersThroughput | RU for users container | 400 |
| charactersThroughput | RU for characters container | 400 |
| entraApiAudience | API App identifier URI | api://<API_APP_ID> |
| entraTenantId | Tenant GUID | 00000000-... |
| entraB2cPolicy | Optional B2C user flow | B2C_1_SIGNUPSIGNIN |
| entraB2cPrimaryDomain | B2C primary domain | yourtenant.onmicrosoft.com |
| spaClientId | Frontend client id | <SPA_APP_ID> |
| spaApiScope | Scope string (.default or named) | api://<API_APP_ID>/.default |
| allowedOrigins | CORS (comma list) | <https://app.example.com> |

### 15.2 Outputs

| Output | Description | Usage |
|--------|-------------|-------|
| apiFqdn | Public FQDN of API container app | Configure frontend API base URL |
| webFqdn | Public FQDN of web container app | Post‑deploy verification |
| cosmosEndpoint | Cosmos DB endpoint URI | Diagnostic/reference |

### 15.3 azure.yaml Enhancements

`azure.yaml` declares services `api` and `web`, placeholder environment variables, and an infra parameters block. Sensitive values (client IDs, scopes, tenant, policy) should be set via `azd env set` not committed.

### 15.4 Suggested azd Workflow

```bash
azd env new dev

azd env set prefix nchat
azd env set environment dev
azd env set acrName acrnchatdev
azd env set entraApiAudience api://<API_APP_ID>
azd env set entraTenantId <TENANT_GUID>
azd env set spaClientId <SPA_APP_ID>
azd env set spaApiScope api://<API_APP_ID>/.default
azd env set allowedOrigins https://localhost:3000
azd env set entraB2cPolicy B2C_1_SIGNUPSIGNIN
azd env set entraB2cPrimaryDomain yourtenant.onmicrosoft.com

azd up

# Subsequent code-only deployments
azd deploy

# Show outputs
azd env get-values | grep apiFqdn

# Tear down
azd down
```

### 15.5 Image Tagging Strategy

Current Bicep references `:latest`. Improve determinism by tagging images with git SHA and parameterizing image tags in Bicep (future enhancement: add `apiImageTag`, `webImageTag`).

### 15.6 Secrets & Security Roadmap

| Concern | Current | Future |
|---------|---------|--------|
| Cosmos key handling | Container App secret | Managed Identity + RBAC |
| ACR auth | Username/password secret | Managed Identity (AcrPull role) |
| Config values | Plain env vars | Key Vault references |

### 15.7 Post‑Provision Verification

| Check | Command | Expect |
|-------|---------|--------|
| API health | `curl https://$(azd env get-value apiFqdn)/healthz` | 200 |
| Frontend reachable | Open `https://$(azd env get-value webFqdn)` | App loads |
| Auth redirect | Click Sign In | Redirect to login page |

### 15.8 Cleanup

Use `azd down` to delete all provisioned resources safely.


## 16. Social Sign-In & B2C Configuration Runbook (Detailed)

This section is an actionable, linear checklist to enable email + Google + (future) Twitter & Discord sign-in using Microsoft Entra External ID (B2C) with the existing codebase.

### 16.1 Prerequisites

- Azure subscription owner or appropriate directory roles (to create External ID tenant & app registrations).
- Chosen tenant for B2C (or create a new External ID tenant if you have not already).
- Ability to create OAuth credentials in Google, Twitter, Discord developer portals.

### 16.2 Create / Identify External ID (B2C) Tenant

1. In Azure Portal: Search "External Identities" > (If needed) Create a new tenant (note primary domain: `<tenant>.onmicrosoft.com`).
1. Record:

- Primary domain (`ENTRA_B2C_TENANT_PRIMARY_DOMAIN`).
- Tenant name prefix (for authority derivation) – usually the left part before `.onmicrosoft.com`.

### 16.3 Register the API Application (Resource)

1. Go to (External ID) tenant > App registrations > New registration.
1. Name: `nchat-api` (environment suffix optional).
1. Account type: "Accounts in this organizational directory only" (unless cross-tenant needed).
1. Redirect URIs: None required for pure resource API.
1. After creation: Expose an API > Set Application ID URI to `api://<API_APP_ID>` (portal may suggest format). Save.
1. Add scope:

- Scope name: `access`
- Admin consent display: `Access Naughty Chats API`
- User consent display: `Access Naughty Chats API`
- State: Enabled.

1. Record:

- API App ID (client ID)
- Application ID URI (should be `api://<API_APP_ID>`)

### 16.4 Register the SPA Application (Client)

1. App registrations > New registration.
1. Name: `nchat-spa`.
1. Account type: Same as API (internal) or multi-tenant if required.
1. Redirect URIs (SPA):

- `http://localhost:3000`
- `https://<webFqdn>` (from Bicep output once provisioned) – can add later.

1. Authentication blade:

- Enable SPA platform (implicit not required; we do Auth Code + PKCE automatically via MSAL).
- (Optional) Front-channel logout URL (e.g., `https://<webFqdn>/signout`).

1. API permissions:

- Add permission > My APIs > Select `nchat-api` > check the `access` scope.
- Grant admin consent.

1. Record SPA Client ID.

### 16.5 Create B2C User Flow (Sign Up & Sign In)
1. External Identities > User flows > New user flow.
1. Recommended flow type: "Sign up and sign in".
1. Name: `B2C_1_SIGNUPSIGNIN`.
1. Identity providers (initial): Email signup (local accounts). Select attributes: `email`, `displayName`, `oid`.
1. Multifactor: Enable if required (optional initial).
1. Create.
1. Note Policy name exactly (case sensitive for authority path).

### 16.6 Add Google Provider
1. Google Cloud Console > Create OAuth consent screen + credentials (Web app). Authorized redirect URI: `https://<tenant>.b2clogin.com/<tenant>.onmicrosoft.com/oauth2/authresp` (portal usually displays exact value in provider creation blade) – copy from Azure portal instructions.
1. External Identities > Identity providers > Add provider > Google.
1. Paste Client ID & Secret.
1. Save and then edit the user flow: enable Google provider.

### 16.7 Prepare Twitter & Discord (Future)
Because Twitter & Discord may not present full OIDC metadata, choose one:
1. Attempt custom OpenID Connect provider if provider supports standard discovery (Discord often partial).
2. Otherwise implement an intermediary token exchange (NOT yet in scope). For now, UI keeps buttons disabled or routes all to generic login.

### 16.8 Authority & Configuration (Frontend)
Derived authority format:
```
https://<tenantPrefix>.b2clogin.com/<primaryDomain>/<policy>/v2.0
```
Set variables (local dev example):
```
NEXT_PUBLIC_ENTRA_CLIENT_ID=<SPA_APP_ID>
NEXT_PUBLIC_ENTRA_API_SCOPE=api://<API_APP_ID>/.default
NEXT_PUBLIC_B2C_TENANT_NAME=<tenantPrefix>
NEXT_PUBLIC_B2C_USER_FLOW=B2C_1_SIGNUPSIGNIN
NEXT_PUBLIC_ENTRA_TENANT_ID=<Directory (tenant) ID>
```
Optionally override with:
```
NEXT_PUBLIC_ENTRA_AUTHORITY=https://<tenantPrefix>.b2clogin.com/<primaryDomain>/B2C_1_SIGNUPSIGNIN/v2.0
```

### 16.9 Backend Environment Variables
```
ENTRA_TENANT_ID=<Directory ID>
ENTRA_API_AUDIENCE=api://<API_APP_ID>
ENTRA_B2C_POLICY=B2C_1_SIGNUPSIGNIN
ENTRA_B2C_TENANT_PRIMARY_DOMAIN=<tenantPrefix>.onmicrosoft.com
# Optional strict override:
# ENTRA_EXPECTED_ISSUER=https://<tenantPrefix>.b2clogin.com/<primaryDomain>/B2C_1_SIGNUPSIGNIN/v2.0
```

### 16.10 Updating the Signup / Signin Pages
Replace manual form submit with a single MSAL redirect call (example pseudo):
```tsx
// in signup/page.tsx or signin/page.tsx
const login = () => instance.loginRedirect({ scopes: [process.env.NEXT_PUBLIC_ENTRA_API_SCOPE!] });
```
Hide / remove password inputs once B2C is live to avoid UX confusion.

### 16.11 Token Validation (Already Implemented)
Backend auto-derives JWKS endpoint from policy + domain. Ensure logs show a successful JWKS fetch at cold start.

### 16.12 Smoke Test Flow
1. Navigate to web FQDN, click Sign In.
2. Redirect should display B2C hosted UI with Email + Google.
3. Complete Google signup.
4. After redirect, MSAL acquires token silently; network tab should show call to `/.well-known/openid-configuration` and token endpoints.
5. Invoke a protected fetch (e.g., `/api/me`). Expect 200 with user object.
6. Cosmos users container should contain newly provisioned user doc.

### 16.13 Common Failure Modes
| Symptom | Cause | Resolution |
|---------|-------|------------|
| 401 from API with valid login | Audience mismatch | Confirm API scope & `ENTRA_API_AUDIENCE` identical (no trailing slash) |
| loginRedirect loops | Policy name typo | Verify `B2C_1_SIGNUPSIGNIN` matches portal listing |
| Google missing on page | Not enabled in user flow | Edit user flow > Identity providers |
| acquireTokenSilent fails `no account` | App not handling redirect | Ensure `PublicClientApplication` handles `handleRedirectPromise()` in provider code |

### 16.14 azd Environment Parameterization (Quick Reference)
Run after all IDs gathered:
```
azd env new dev
azd env set prefix nchat
azd env set environment dev
azd env set acrName acrnchatdev
azd env set entraTenantId <TENANT_ID>
azd env set entraApiAudience api://<API_APP_ID>
azd env set spaClientId <SPA_APP_ID>
azd env set spaApiScope api://<API_APP_ID>/.default
azd env set entraB2cPolicy B2C_1_SIGNUPSIGNIN
azd env set entraB2cPrimaryDomain <tenantPrefix>.onmicrosoft.com
azd env set allowedOrigins https://<webFqdn>,http://localhost:3000
azd up
```

### 16.15 Post-Configuration Checklist
- [ ] Google sign-in works end-to-end.
- [ ] User document created in Cosmos.
- [ ] `/api/me` returns correct email.
- [ ] Audience & issuer logged once at API start (no repeating fetch on each call).
- [ ] No hard‑coded secrets remaining in code.

---
End of extended runbook.


