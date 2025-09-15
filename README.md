# Naughty Chats

FastAPI + Next.js application deployed on Azure Container Apps with Microsoft Entra ID / External ID (B2C) authentication and Cosmos DB for persistence. Extensible for social identity (Google, Twitter, Discord) via Entra External ID.

## High-Level Architecture

```text
[ Browser ] -- MSAL --> Entra ID / B2C (Hosted UI)
|                               |
| access token                  |
v                               v
Next.js (web)  ---- REST ----> FastAPI (api) ----> Cosmos DB
   |  (deploy)            (deploy)           (NoSQL containers)
   +----> Azure Container Apps <----+ Log Analytics
                 |
                 +---- Azure Container Registry (images)
```

## Auth Flow Summary

1. User clicks Sign In → redirected to Entra (or B2C user flow with social providers).
2. After authentication MSAL stores tokens; frontend acquires API scope.
3. Backend validates token (issuer, signature, audience) using dynamic JWKS.
4. If user does not exist, backend creates a user document (auto-provisioning).

## Repository Structure

| Path | Description |
|------|-------------|
| `backend/` | FastAPI service, auth validation, Cosmos integration |
| `frontend/` | Next.js app (App Router), MSAL provider |
| `infra/` | `main.bicep` defining Azure resources |
| `azure.yaml` | azd project + services definition |
| `deployment.md` | Comprehensive deployment & configuration guide |

## Quickstart (Local Dev)

Prerequisites: Python 3.11+, Node 20+, Azure CLI (optional), Entra tenant + two app registrations.

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export COSMOS_ENDPOINT=http://localhost:8081 # if using emulator
export COSMOS_KEY=localKey
export COSMOS_DATABASE=nchatsdb
export COSMOS_USERS_CONTAINER=users
export COSMOS_CHARACTERS_CONTAINER=characters
export ENTRA_TENANT_ID=<TENANT_GUID>
export ENTRA_API_AUDIENCE=api://<API_APP_ID>
uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
export NEXT_PUBLIC_ENTRA_CLIENT_ID=<SPA_APP_ID>
export NEXT_PUBLIC_ENTRA_TENANT_ID=<TENANT_GUID>
export NEXT_PUBLIC_ENTRA_API_SCOPE=api://<API_APP_ID>/.default
npm run dev
```

Visit <http://localhost:3000>.

To enable B2C/social, also set (both sides):

```bash
export ENTRA_B2C_POLICY=B2C_1_SIGNUPSIGNIN
export ENTRA_B2C_TENANT_PRIMARY_DOMAIN=yourtenant.onmicrosoft.com
export NEXT_PUBLIC_B2C_TENANT_NAME=yourtenant
export NEXT_PUBLIC_B2C_USER_FLOW=B2C_1_SIGNUPSIGNIN
```

## Infrastructure Deployment (azd)

Refer to `deployment.md` Section 15 for full details.

Minimal flow:

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
azd up
```

Outputs (e.g., `apiFqdn`, `webFqdn`) can be retrieved:

```bash
azd env get-values | grep apiFqdn
```

## Testing

Auth tests use synthetic RSA keys & mocked JWKS: see `backend/tests/test_auth.py`.
Run:

```bash
cd backend
pytest -q
```

## Future Enhancements

- Key Vault + Managed Identity (remove Cosmos key secret)
- App Insights + OpenTelemetry tracing
- Image tag parameterization (Git SHA)
- Enhanced RBAC & scope separation
- Pagination & RU optimization

## License

Proprietary / Internal (update this section if open-sourcing).
