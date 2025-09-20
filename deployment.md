# Naughty Chats — Deployment Reference (concise)

This file is a compact, table-oriented reference for deploying Naughty Chats to Azure (Container Apps + ACR + Cosmos + Entra). It contains the canonical resource names, environment variable mappings, secrets, and the exact az CLI commands needed to discover and set values.

> Keep secrets out of source control. Use Key Vault for production; Container App secrets are acceptable for quick deployments.

---

## 1 — Canonical resources (current environment)

| Category | Name (example) | Current value / note |
|---|---:|---|
| Subscription | Visual Studio Enterprise Subscription | id: 9147ac3b-6cf8-4f04-b959-89b59dd706d3 |
| Resource group | rg-nchat-dev | |
| Container Apps environment | cae-nchat-dev | |
| Web Container App | web-nchat-dev | FQDN: web-nchat-dev.victoriouswave-309ecfc3.eastus.azurecontainerapps.io |
| API Container App | api-nchat-dev | FQDN: api-nchat-dev.victoriouswave-309ecfc3.eastus.azurecontainerapps.io |
| ACR (login server) | acrnchatdev | acrnchatdev.azurecr.io |
| Cosmos account | cosmos-nchat-dev-cu | URI: https://cosmos-nchat-dev-cu.documents.azure.com:443/ |
| Log Analytics workspace | law-nchat-dev | used by container app env |

---

## 2 — Entra (App registrations)

| App role | Display name | Application (client) ID | Application ID URI / notes |
|---|---:|---:|---|
| API (resource) | NaughtyChats API | 2b3282d9-d672-4c1e-b963-0d3235cb0f31 | Application ID URI: api://2b3282d9-d672-4c1e-b963-0d3235cb0f31 |
| SPA (frontend) | NaughtyChats SPA | bf515dbe-ecdb-4382-b1f8-ee8d911d5795 | Used as NEXT_PUBLIC_ENTRA_CLIENT_ID |
| Other app(s) | NaughtyChatsAI (examples) | ff391c40-67ad-4eba-ac9c-8793ad579e5e | May contain redirect URIs, check Auth settings |

---

## 3 — Environment variables mapping (what to set where)

Backend (api container app) — recommended to set as env vars and store secrets in Key Vault or Container App secrets:

| Name | Purpose | Stored as |
|---|---|---|
| COSMOS_ENDPOINT | Cosmos DB URI | env var (value or secretref) |
| COSMOS_KEY | Cosmos primary key | secret (Key Vault or Container App secret name `cosmos-key`) |
| COSMOS_DATABASE | DB name (nchatsdb) | env var |
| COSMOS_USERS_CONTAINER | users container | env var |
| COSMOS_CHARACTERS_CONTAINER | characters container | env var |
| ALLOWED_ORIGINS | CORS (comma-separated) | env var |
| ENTRA_TENANT_ID | Tenant id | env var |
| ENTRA_API_AUDIENCE | API Application ID URI | env var |
| ENTRA_B2C_POLICY | (if B2C) user flow | env var (optional) |

Frontend (web container app) — public settings and server secrets for NextAuth:

| Name | Purpose | Stored as |
|---|---|---|
| NEXT_PUBLIC_API_BASE_URL | API base URL | env var |
| NEXT_PUBLIC_ENTRA_CLIENT_ID | SPA client id | env var |
| NEXT_PUBLIC_ENTRA_API_SCOPE | API scope for token acquisition | env var |
| NEXT_PUBLIC_B2C_TENANT_NAME | B2C tenant short name (optional) | env var |
| NEXT_PUBLIC_B2C_USER_FLOW | B2C user flow/policy (optional) | env var |
| AZURE_AD_CLIENT_ID | (server) confidential client id used by NextAuth | env var |
| AZURE_AD_CLIENT_SECRET | (server) confidential client secret | secret (Key Vault or Container App secret name `azure-ad-client-secret`) |
| NEXTAUTH_SECRET | NextAuth signing secret | secret (Key Vault or Container App secret name `nextauth-secret`) |
| NEXTAUTH_URL | Public site URL for callbacks | env var |

---

## 4 — Secrets (names & where to create)

| Secret name | Intended container app | Recommended storage |
|---|---:|---|
| cosmos-key | api-nchat-dev | Key Vault secret `kv/...` or Container App secret `cosmos-key` |
| azure-ad-client-secret | web-nchat-dev | Key Vault or Container App secret |
| nextauth-secret | web-nchat-dev | Key Vault or Container App secret |
| jwt-secret | api-nchat-dev (legacy) | Container App secret if used |

Notes: Portal / az will not return secret values after creation. Store immediately if you create a client secret in App Registrations.

---

## 5 — Quick az CLI commands (discovery & set)

Discovery commands (read-only):

- Subscription: az account show -o json
- Web FQDN: az containerapp show -n web-nchat-dev -g rg-nchat-dev --query properties.configuration.ingress.fqdn -o tsv
- API FQDN: az containerapp show -n api-nchat-dev -g rg-nchat-dev --query properties.configuration.ingress.fqdn -o tsv
- Web env vars: az containerapp show -n web-nchat-dev -g rg-nchat-dev --query properties.configuration.template.containers[0].env -o json
- API secrets (names): az containerapp show -n api-nchat-dev -g rg-nchat-dev --query properties.configuration.secrets -o json
- ACR login server: az acr show -n acrnchatdev -g rg-nchat-dev --query loginServer -o tsv
- App registrations (Graph): az rest --method GET --uri "https://graph.microsoft.com/v1.0/applications?$filter=contains(displayName,'nchat')"
- Cosmos endpoint: az cosmosdb show -g rg-nchat-dev -n cosmos-nchat-dev-cu --query documentEndpoint -o tsv

Set a Container App secret (example):

- az containerapp secret set -n api-nchat-dev -g rg-nchat-dev --secrets cosmos-key='<primary-key-value>'
- Link secret to env (example): az containerapp update -n api-nchat-dev -g rg-nchat-dev --set-env-vars COSMOS_KEY=secretref:cosmos-key

Create a server client secret (App Registration):

- az ad app credential reset --id <server-app-client-id> --append --display-name "nchat-server-secret"
  - Save the returned `password` value immediately — it is never shown again.

Important: To call Microsoft Graph (`az rest` above) you may need Directory.Read.All permission for the account or be an admin.

---

## 6 — Minimal deploy checklist (one-page)

1. Ensure `az login` and the right subscription selected: az account show
2. Confirm Container Apps FQDNs and envs (see commands section)
3. Create or provide secrets:
   - Generate NEXTAUTH_SECRET: openssl rand -hex 32
   - Create server client secret if needed: az ad app credential reset --id <server-app-client-id>
   - Add COSMOS_KEY (value) to API container app as secret
4. Update deploy script invocation with values (or run deploy script with flags):
   - Required args: --resource-group rg-nchat-dev --acr acrnchatdev --api-app api-nchat-dev --web-app web-nchat-dev --spa-client-id <SPA_ID> --api-scope <API_SCOPE> --tenant-name <tenant> --user-flow <policy> --azure-client-secret <secret> --nextauth-secret <secret>
5. Run deploy (dry-run first): python3 scripts/deploy.py --env dev --region eastus --resource-group rg-nchat-dev --acr acrnchatdev --api-app api-nchat-dev --web-app web-nchat-dev --spa-client-id <SPA_ID> --api-scope <API_SCOPE> --tenant-name <tenant> --user-flow <policy> --azure-client-secret <secret> --nextauth-secret <secret> --skip-build --dry-run
6. If dry-run looks good, run without --dry-run (and without --skip-build if you want to build images).
7. Verify rollout: check container app revisions and hit /healthz and /api/me after signing in.

---

## 7 — If you want me to proceed (choices)

- I can run the remaining write commands (set Container App secrets) if you confirm and provide secrets (or allow me to create them). Reply with exact instruction:
  - "store cosmos-key as container secret" or
  - "create server client secret for appId <id> and store it"
- Or I can prepare a PR with these exact commands and leave execution to you.

---

This file intentionally omits verbose background and rationale — it focuses on the single purpose: store and discover the canonical deploy-time values and the exact commands to set them. Keep it updated with current secret names and FQDN values after each deploy.


