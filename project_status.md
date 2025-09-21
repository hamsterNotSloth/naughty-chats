# Project Status

Date: 2025-09-21

Summary

- Current milestone: dev infra and dev container images deployed to Azure Container Instances for manual testing. Backend (FastAPI) and frontend (Next.js static export) are running in ACI and reachable over HTTP (no TLS termination yet).
- Cosmos DB provisioned in Central US (dev); keys stored in Key Vault `nchkvz3df53-2`.
- ACR exists and remote builds were used to build and push images.
- Known gaps before production: TLS termination, private networking (private endpoints), managed identities for runtime, hardened container images, CI/CD with security gates, production-grade Cosmos configuration, observability and alerting.

Live endpoints (dev)

- Backend ACI FQDN: naughty-backend-dev-ysurana.eastus.azurecontainer.io:8080
- Frontend ACI FQDN: naughty-frontend-dev-ysurana.eastus.azurecontainer.io:8080
- ACR: naughtychatsacrz3df53vhag66y.azurecr.io
- Key Vault (dev): nchkvz3df53-2
- Cosmos endpoint (dev): https://naughtychatscosmosz3df53vhag66y.documents.azure.com:443/

Next immediate actions (high priority)

1. Enable HTTPS termination (Front Door or Static Web Apps) and map custom domains.
2. Replace ACR admin credentials with Managed Identity / Service Principal and grant ACI or Container Apps a managed identity for pulling images and accessing Key Vault.
3. Harden backend auth: enable secure cookie only over HTTPS and implement refresh token rotation + revocation list.
4. Move runtime from ACI to Container Apps or App Service for production workflows and easier identity integration.
5. Configure Cosmos DB production settings: private endpoint, autoscale RUs, multi-region, continuous backup.
6. Add Application Insights and Log Analytics with diagnostic settings across resources and configure alerts for SLOs.

Risks & Mitigations

- Public endpoints without TLS: do not store secrets or accept production traffic; mitigate by enabling Front Door and WAF.
- Secrets in Key Vault with admin access: enforce RBAC and least privilege, rotate secrets.
- Cosmos public access: use private endpoints and firewall rules.

Contact

- Repo: hamsterNotSloth/naughty-chats (branch: main)
- Owner: ysurana

