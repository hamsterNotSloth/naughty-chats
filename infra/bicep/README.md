This folder contains Bicep skeletons and modules for deploying Naughty Chats infrastructure to Azure.

Contents
- main.bicep - top-level deployment that composes modules
- modules/
  - cosmosdb.bicep - Cosmos DB account, database and container skeleton
  - containerapp.bicep - Container Apps environment and app skeleton
  - keyvault.bicep - Key Vault skeleton
  - acr.bicep - Azure Container Registry skeleton
  - frontdoor.bicep - Front Door / Application Gateway skeleton

Guidance
- Use Managed Identities for service authentication and avoid storing secrets in code.
- Parameterize location, SKU and environment-specific settings.
- Validate RBAC least-privilege for GitHub Actions service principal.

Deployment
- Validate templates locally with: `az bicep build --file main.bicep`
- Dry-run deployment with: `az deployment group what-if --resource-group <rg> --template-file main.bicep --parameters @env.parameters.json`

Best practices
- Keep modules small and focused.
- Provide parameter files per environment (dev/staging/prod).
- Use secrets in Key Vault and grant access via Managed Identity.
- Monitor RU usage for Cosmos DB and use autoscale if unsure about traffic patterns.
