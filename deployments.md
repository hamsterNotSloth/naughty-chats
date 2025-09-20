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

End of plan
