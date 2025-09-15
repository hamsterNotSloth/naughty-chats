# Deployment Plan: Naughty Chats (FastAPI + Next.js) – Azure (Container Apps + Cosmos DB NoSQL)

## 1. Objectives

Deploy FastAPI API + Next.js frontend to Azure using:

- Azure Container Apps (ACA) for both frontend (SSR) and backend
- Azure Container Registry (ACR) for image storage
- Azure Cosmos DB (Core API / NoSQL) for persistence (users, characters)
- Entra ID for auth (Phase 2 enforcement; Phase 1 local JWT fallback)
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
| Auth | Local JWT (HS256) temporary |
| Seeding | Characters seeded at startup (idempotent) |
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
| Secrets | ACA secrets (Phase 1) | SECRET_KEY, Cosmos key | Migrate to Key Vault + MI |
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

| Phase | Secrets | Cosmos Auth | Network | Auth |
|-------|---------|------------|---------|------|
| 1 | ACA secrets | Primary key | Public endpoint | Local JWT |
| 2 | Key Vault + MI | AAD RBAC | Private Endpoint/VNet | Entra tokens only |

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

Backend:

- SECRET_KEY
- ALLOWED_ORIGINS
- COSMOS_ENDPOINT
- COSMOS_KEY
- COSMOS_DATABASE (default `nchatsdb`)
- COSMOS_USERS_CONTAINER (default `users`)
- COSMOS_CHARACTERS_CONTAINER (default `characters`)
- COSMOS_AUTO_PROVISION (false in cloud)
- ENTRA_TENANT_ID / ENTRA_API_AUDIENCE / ENTRA_JWKS_URL
- LOCAL_AUTH_ENABLED (false in cloud once Entra active)

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
SECRET_KEY_VALUE=$(openssl rand -hex 32)

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
  --secrets secret-key=$SECRET_KEY_VALUE cosmos-endpoint="$COSMOS_ENDPOINT" cosmos-key="$COSMOS_KEY" \
  --env-vars SECRET_KEY=secretref:secret-key COSMOS_ENDPOINT=secretref:cosmos-endpoint COSMOS_KEY=secretref:cosmos-key \
             COSMOS_DATABASE=$COSMOS_DB COSMOS_USERS_CONTAINER=users COSMOS_CHARACTERS_CONTAINER=characters \
             COSMOS_AUTO_PROVISION=false LOCAL_AUTH_ENABLED=false ALLOWED_ORIGINS="https://placeholder" \
             ENTRA_TENANT_ID=TENANT_ID ENTRA_API_AUDIENCE=api://API_APP_ID

API_FQDN=$(az containerapp show -g $RG -n ca-$PREFIX-api-$ENV --query properties.configuration.ingress.fqdn -o tsv)

az containerapp create -n ca-$PREFIX-web-$ENV -g $RG --environment $CAE --image $WEB_IMAGE \
  --target-port 3000 --ingress external \
  --registry-server $ACR_LOGIN --registry-username $ACR_USER --registry-password $ACR_PASS \
  --env-vars NEXT_PUBLIC_API_BASE_URL=https://$API_FQDN NEXT_PUBLIC_ENTRA_CLIENT_ID=SPA_CLIENT_ID \
             NEXT_PUBLIC_ENTRA_TENANT_ID=TENANT_ID NEXT_PUBLIC_ENTRA_API_SCOPE=api://API_APP_ID/.default
```

## 9. Validation Checklist (Executed Phase 1)

| Step | Action | Expected |
|------|--------|----------|
| 1 | curl /healthz | 200 {"status": "ok"} |
| 2 | Frontend characters page | Seeded list visible |
| 3 | Register user | 200 + token; doc in users container |
| 4 | Login + /api/me | Returns user payload |
| 5 | /api/me no token | 401 |
| 6 | (After Entra) Entra token call | 200 |
| 7 | Log Analytics check | Request logs present |
| 8 | Rotate secret-key & restart | Old tokens invalid |

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Primary key leakage | Data exposure | Move to RBAC, rotate key |
| High RU consumption | Throttling / cost | Index tuning, caching |
| Placeholder IDs | Contract churn | Implement real IDs early |
| Missing auth enforcement | Security gap | Add Entra validation |
| Over-broad CORS | Token leakage | Strict production origins |
| No backups | Data loss | Enable continuous backup |
| Secrets lifecycle | Rotation issues | Key Vault + MI |

## 11. Next Steps (Ordered – Updated Priorities)

1. Add readiness & liveness probes (/healthz) to backend Container App
2. Implement real ID propagation in responses
3. Add Entra ID JWT validation & disable local fallback in cloud
4. Introduce Key Vault + Managed Identity + Cosmos RBAC
5. Add App Insights + OpenTelemetry + structured logging (correlation IDs)
6. Author Bicep modules + azure.yaml (azd)
7. Create CI/CD (GitHub Actions) with build+scan+deploy
8. Pagination & index policy optimization (RU tests)

## 12. Environment Variable Matrix

| Scope | Name | Example | Secret | Notes |
|-------|------|---------|--------|-------|
| Backend | SECRET_KEY | (hex) | Yes | Remove if not needed post-Entra |
| Backend | COSMOS_ENDPOINT | <https://cosmos-nchat-dev.documents.azure.com:443/> | Yes | Primary endpoint |
| Backend | COSMOS_KEY | (base64) | Yes | Replace with RBAC |
| Backend | COSMOS_DATABASE | nchatsdb | No | Default fallback |
| Backend | COSMOS_USERS_CONTAINER | users | No |  |
| Backend | COSMOS_CHARACTERS_CONTAINER | characters | No |  |
| Backend | COSMOS_AUTO_PROVISION | false | No | Only true for local dev bootstrap |
| Backend | ALLOWED_ORIGINS | <https://app.example.com> | No | Comma separated |
| Backend | ENTRA_TENANT_ID | GUID | No | Needed Phase 2 |
| Backend | ENTRA_API_AUDIENCE | api://API_APP_ID | No | Audience claim |
| Backend | ENTRA_JWKS_URL | <https://login.microsoftonline.com/TENANT_ID/discovery/v2.0/keys> | No | Override only if necessary |
| Backend | LOCAL_AUTH_ENABLED | false | No | False in cloud |
| Frontend | NEXT_PUBLIC_API_BASE_URL | <https://ca-nchat-api-dev.REGION.azurecontainerapps.io> | No | Public runtime |
| Frontend | NEXT_PUBLIC_ENTRA_CLIENT_ID | GUID | No | Public |
| Frontend | NEXT_PUBLIC_ENTRA_TENANT_ID | GUID | No | Public |
| Frontend | NEXT_PUBLIC_ENTRA_API_SCOPE | api://API_APP_ID/.default | No | Public |

Suggested secret names: `secret-key`, `cosmos-endpoint`, `cosmos-key`.

