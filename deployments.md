16) Azure Deployment Plan (detailed)

Overview

We will deploy production infrastructure to Azure using IaC (Bicep). The goal is secure, cost-aware, scalable, and observable infrastructure that aligns with the architecture in this document. Components map to Azure managed services to reduce operational overhead and provide enterprise-grade SLAs.

Primary Azure Resources

- Resource Groups: two RGs only — `dev` and `prod`.
- Azure Container Apps: run both frontend (Next.js container) and backend (FastAPI API + worker containers). Use separate Container Apps or revisions per role.
- Azure Cosmos DB (Core SQL API): primary OLTP/document store for users, characters, chats, messages, gem_ledger (event-sourced), gen_jobs, images, affiliates, moderation_items and idempotency records. Design for per-user partitioning.
- Azure Blob Storage: store generated images, thumbnails, and large artifacts. Use private blob containers + SAS URLs.
- Azure Key Vault: store secrets (Cosmos keys, provider keys, stripe secret, runpod tokens).
- Azure Application Gateway / Front Door: global ingress, WAF, TLS termination and routing to Container Apps.
- Azure Monitor & Log Analytics workspace: collect logs and metrics; use Application Insights for traces.
- Azure Service Bus: durable messaging for image generation and background job orchestration.
- Azure Storage Account for backups & snapshots: daily backups of DB exports and blob snapshots.
- Azure Container Registry (ACR): host docker images.
- Managed Identities: assigned to Container Apps/other services to access Key Vault and Storage.

Network & Security

- VNet Integration: provision Virtual Network and integrate Cosmos DB private endpoint, Key Vault and Storage to minimize public exposure. Container Apps will use VNet integration to access private endpoints.
- Private Endpoints: for Cosmos DB, Key Vault and Storage to avoid public exposure.
- NSGs: restrict inbound/outbound as appropriate.
- WAF & DDoS: configure Application Gateway WAF policies and enable DDoS Basic/Standard as needed.
- Firewall rules: Cosmos DB and Storage firewall restricted to VNet and allowed management IPs.
- TLS & Certs: use managed certs via Front Door / App Gateway.

Identity & Secrets

- Use Azure Entra ID for authentication, and configure Entra federation for Google and Discord social logins (OAuth through Entra). Keep JWT refresh/access flows in backend but leverage Entra for social auth federation and token introspection as needed.
- Key Vault with RBAC and access policies.
- Managed Identities for Container Apps: allow access to Key Vault & Storage via role assignments rather than storing secrets.
- GitHub Actions runner integration: allow GH Actions to deploy via a service principal with minimal permissions (create/update deployments, ACR push, resource group deployment).

High-Availability & Scaling

- Cosmos DB (Core SQL API): configure multi-region writes and appropriate RU/s or autoscale throughput. Use partitioning strategy (per-user) and enable zone redundancy.
- Container Apps: scale based on CPU, memory, and custom metrics (queue length, active websocket connections). Use separate revisions for api and worker images with controlled traffic routing.
- Blob Storage: RA-GRS for resilience if required; lifecycle management for cost.

CI/CD & IaC

- Bicep templates under infra/bicep/ with modules for each resource.
- GitHub Actions workflows:
  - ci.yml: lint, unit tests, build docker images, push to ACR.
  - deploy.yml: deploy Bicep ARM templates to target RG (staging/prod) with parameterized environments and approve gates for production.
  - migrate.yml: migrations or data transform jobs for Cosmos DB (if needed) as part of deploy step.
- Secrets for deployment in GitHub Secrets (SPN credentials), and deployments use Managed Identity where possible.

Monitoring & SLO mapping

- Application Insights: trace request durations, exceptions, dependencies. Instrument chat first token latency and generation accept latency as custom metrics.
- Log Analytics: aggregate structured logs and set queries/alerts.
- Alerts & Actions:
  - Alert chat_first_token_p95 > 4s -> paging to oncall
  - Alert gen_queue_depth > threshold -> oncall + autoscale workers
  - Alert error_rate_5m > X% -> Slack + oncall
- Dashboards: API latency, worker queue length, Cosmos DB RU usage, blob storage usage, payment webhook lag.

Backups & DR

- Cosmos DB: enable continuous backup (point-in-time restore) and configure retention per environment. Use zone-redundant or geo-redundant options according to requirements.
- Blob snapshots retained per lifecycle policy for 30 days; critical images may have longer retention.
- Disaster Recovery runbook: steps to restore Cosmos DB from backup, rotate keys, reattach Storage and re-deploy Container Apps.

Cost Estimation & Controls

- Use Azure Cost Management to track spend per RG.
- Tags: enforce resource tagging for owner, environment, project.
- Use auto-scaling with conservative min/max to control costs. Use burstable SKU for dev where applicable.
- Estimate starting monthly baseline: Cosmos DB (RU-based or autoscale) + 2 Container Apps instances + ACR + Blob Storage ~ modest amount; provide more accurate numbers once sizing & traffic estimates provided.

Operational Runbooks (Azure-specific)

- Rotate Key Vault secrets: use Key Vault versions, update apps by restarting Container Apps revision.
- Scaling workers: increase Container Apps replica counts or allow autoscale based on queue length metric; fallback to scale-up plan (larger SKU) if autoscale insufficient.
- Replace Cosmos DB instance: create new Cosmos account, restore from backup/restore, update connection strings in Key Vault, roll Container Apps revision.
- Emergency deny: block Front Door routing to app by toggling routing rule (for incident containment).

Migration & Rollout Strategy

- Blue/Green or Canary deployment via Container Apps revisions.
- Data migrations: perform non-destructive transforms; use backfill strategies and versioned document formats to maintain backward compatibility.
- Feature flags for risky features (image gen, payments) to allow quick toggles without code redeploy.

Next Steps (Azure deliverables)

- Create Bicep module skeletons for core infra: Cosmos DB, Key Vault, Container Apps, ACR, Front Door.
- Add GitHub Actions deploy pipeline that validates Bicep and can run in dry-run mode.
- Create Managed Identity and role assignment script for GH Actions.
- Produce cost estimate with realistic traffic numbers.

## Resource Groups — Detailed (dev and prod)

This section expands the short line in the plan "Resource Groups: two RGs only — `dev` and `prod`" into explicit, production-ready definitions. Use the examples below as canonical names and a template for Bicep parameterization. Replace placeholders with your real Subscription IDs and DNS names when deploying.

### Naming conventions and general rules

- RG naming:
  - Dev: `naughty-chats-dev-rg`
  - Prod: `naughty-chats-prod-rg`
- Locations (examples):
  - Primary region: `centralus` (for low-latency to Cosmos primary)
  - Secondary/DR region: `eastus` (read replica / failover)
- Tags: every resource must include tags: `project=naughty-chats`, `env=dev|prod`, `owner=<owner-email>`, `cost-center=<cc>`.
- Subscription: use separate subscriptions if organization policy requires strict isolation between dev and prod or large-scale financial separation. At minimum separate RGs per environment.

### Resource group: naughty-chats-dev-rg (detailed)

Purpose: development and integration testing. Lower cost SKUs, may permit public endpoints for rapid iteration, but still follow security hygiene.

Recommended contents (explicit resources and naming):

- Networking
  - VNet: `nch-dev-vnet` (address space 10.10.0.0/16)
  - Subnets:
    - `app-subnet` (10.10.10.0/24) — for Container Apps or ACI egress
    - `db-subnet` (10.10.20.0/24) — for Cosmos private endpoint
    - `infra-subnet` (10.10.30.0/24) — for management jumpboxes or VM-based tools
  - NSGs: `nch-dev-nsg-app`, `nch-dev-nsg-db` with least-privileged rules
  - Private DNS zone: `privatelink.documents.azure.com` and link to VNet for Cosmos private endpoint resolution

- Identity & secrets
  - Key Vault: `nch-dev-kv` (soft-delete enabled, purge protection enabled depending on policy)
  - Managed Identities:
    - `msi-naughty-backend-dev` assigned to Container Apps / Container Group
    - `msi-github-deploy-dev` for CI (if needed) with only contributor rights on the RG

- Compute & runtime
  - Container Apps Environment: `nch-dev-ca-env`
  - Container Apps:
    - `nch-backend-dev` (FastAPI container, scaled to 0-3, CPU/memory limits parameterized)
    - `nch-frontend-dev` (static front-end container)
  - Alternatively ACI debug containers: `nch-backend-debug` (do not use for prod)

- Storage & Data
  - Cosmos DB (dev account): `nch-dev-cosmos` (single-region or limited RU autoscale)
  - Blob Storage: `nchdevstorage` (private containers + SAS for test assets)
  - Service Bus (dev): `nch-dev-sb` (namespaces for job orchestration)

- CI/CD & registry
  - ACR (dev): `nchdevacr` (or shared ACR in central subscription)
  - GitHub Actions secrets: limited SPN or OIDC-based tokens for push

- Observability
  - Log Analytics Workspace: `nch-dev-law`
  - Application Insights instance: `nch-dev-ai` (instrumentation key saved in Key Vault or via Managed Identity)

- Policies & budgets
  - Policy assignments: restrict public IP creation except for approved resources, enforce tag policies
  - Budget: set `nch-dev-budget` with alert thresholds at 50%/75%/90%

- Access & RBAC
  - Dev team: Reader or Contributor on dev RG as appropriate
  - CI Service Principal: `contributor` with scope limited to RG for infra and ACR push

### Resource group: naughty-chats-prod-rg (detailed)

Purpose: production traffic, high-availability, security-hardened, audited.

Core design principles: private networking (private endpoints), managed identities only, least privilege, autoscale RUs and instances, multi-region failover, observability and alerting, WAF and TLS termination.

Recommended contents (explicit resources and naming):

- Networking
  - VNet: `nch-prod-vnet` (address space 10.20.0.0/16)
  - Subnets:
    - `app-subnet` (10.20.10.0/24) — for Container Apps egress
    - `db-subnet` (10.20.20.0/24) — for Cosmos private endpoint
    - `infra-subnet` (10.20.30.0/24) — for management services
  - NSGs: `nch-prod-nsg-app`, `nch-prod-nsg-db` with inbound rules only from Front Door/Ingress IPs
  - Private DNS zones and Private Endpoint DNS: configure privatelink for Cosmos, Key Vault and Storage
  - UDRs (User Defined Routes): route egress through security appliances or NAT if required

- Identity & secrets
  - Key Vault: `nch-prod-kv` (soft-delete on, purge protection on)
  - Managed Identities:
    - `msi-naughty-backend-prod` assigned to Container Apps / App Service
    - System-assigned identities for individual services where applicable
  - Entra roles: define groups for oncall/devops and grant least privilege

- Compute & runtime
  - Container Apps Environment: `nch-prod-ca-env` or App Service Plan + App for API
  - Container Apps / Revisions:
    - `nch-backend` (FastAPI) — production revision with autoscale based on CPU/RAM and custom metrics (queue length)
    - `nch-workers` (background job workers) — scale by queue depth
    - `nch-frontend` — static site delivered via Front Door origin or Azure Static Web Apps
  - Consider App Service for backend if easier TLS & identity integration is preferred

- Ingress, TLS & WAF
  - Azure Front Door (or Application Gateway + WAF): `nch-frontdoor-prod`
    - Custom domain(s): `app.example.com`, `api.example.com`
    - Managed TLS certificates
    - Health probes pointing to backend readiness/health endpoints
    - WAF ruleset: OWASP 3.2 baseline + custom rules to block abusive patterns

- Storage & Data
  - Cosmos DB (prod account): `nch-prod-cosmos` — configure:
    - Multi-region writes or geo-replication reads (as required)
    - Autoscale RU configuration and max RU cap
    - Continuous backup (PITR) and retention policy
    - Private endpoint and firewall restrictions
    - Consistency policy (Session/Strong as required by features)
  - Blob Storage account(s): `nchprodstorage` with soft-delete, lifecycle rules and replication (GZRS/RA-GRS as required)
  - Service Bus namespace: `nch-prod-sb` (with claims-based access via Managed Identities)

- Container Registry & image security
  - ACR: `nch-prod-acr` — enable Content Trust, set retention policy, run vulnerability scan during CI (Trivy/ACR Tasks)
  - Disable ACR admin user; use MSI or Service Principal for push/pull

- Observability
  - Log Analytics Workspace: `nch-prod-law` (centralized)
  - Application Insights: `nch-prod-ai` with distributed tracing and sampling
  - Diagnostic settings: route resource diagnostics (App Gateway, Container Apps, Storage, Cosmos) to Log Analytics and to a storage account for long-term retention
  - Alerts: implement the SLO alerts listed in this document

- Backup, DR & Recovery
  - Cosmos continuous backup: configure retention window and test restore playbook quarterly
  - Storage account immutable snapshots for critical artifacts
  - Regular export of critical data to backup subscription/storage

- Security & governance
  - Network: Private Endpoints for Cosmos, Key Vault, Storage — block public network access
  - RBAC: least privilege on Key Vault and other resources; require Privileged Identity Management for high privileges
  - Policy: Enforce tags, allowed locations, required diagnostic settings and firewall rules via Azure Policy assignments
  - NSG/Azure Firewall: limit inbound to Front Door IP ranges and approved management IPs
  - DDoS Protection Standard on subscriptions serving production traffic

- Budgets & Cost Controls
  - Prod budget: `nch-prod-budget` with automated notifications on threshold breach
  - Scaling caps and RU limits to control runaway cost

### Parameterization for IaC (Bicep recommendations)

- Create a `rgParameters` file per environment with the following keys:
  - `subscriptionId`
  - `resourceGroupName`
  - `location`
  - `tags` object
  - `vnetAddressSpace`, `subnetPrefixes` for each subnet
  - `cosmosConfig` object (throughputAutoscale, consistency, regions)
  - `frontDoorConfig` (customDomain, diagnostic settings)

- Bicep modules should take in RG-level parameters and produce outputs for downstream modules (Key Vault URI, VNet id, subnet ids, private endpoint ids, managed identity principalIds).

### Operational notes

- All production RG changes must go through GitHub Actions with required approvals. Never perform ad-hoc manual changes in prod without PR and a rollback plan.
- Configure diagnostic settings to send logs to Log Analytics and an immutable storage container for forensic retention.
- Periodically (quarterly) test cross-region failover and restore procedures.

End of plan
