# Deployment Guide - Naughty Chats

This guide covers deploying the Naughty Chats application to Azure using Infrastructure as Code (Bicep) and GitHub Actions.

## Prerequisites

1. **Azure Subscription** with sufficient permissions to create resources
2. **Azure CLI** installed locally for manual operations
3. **GitHub repository** with secrets configured
4. **Service Principal** for GitHub Actions authentication

## GitHub Secrets Configuration

Configure the following secrets in your GitHub repository (Settings > Secrets and variables > Actions):

```
# Azure Authentication
AZURE_CREDENTIALS='{"clientId": "xxx", "clientSecret": "xxx", "subscriptionId": "xxx", "tenantId": "xxx"}'
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_CLIENT_ID=your-service-principal-client-id
AZURE_CLIENT_SECRET=your-service-principal-secret
AZURE_TENANT_ID=your-tenant-id

# Resource Groups
AZURE_DEV_RG=naughty-chats-dev-rg
AZURE_PROD_RG=naughty-chats-prod-rg

# Container Registry
ACR_LOGIN_SERVER=naughtychatsacrxxx.azurecr.io
ACR_USERNAME=naughtychatsacrxxx
ACR_PASSWORD=your-acr-password
```

## Service Principal Setup

Create a service principal with contributor access to your subscription:

```bash
# Create service principal
az ad sp create-for-rbac --name "naughty-chats-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth

# The output JSON should be stored as AZURE_CREDENTIALS secret
```

## Resource Group Setup

Create resource groups for different environments:

```bash
# Development environment
az group create --name naughty-chats-dev-rg --location eastus

# Production environment  
az group create --name naughty-chats-prod-rg --location eastus
```

## Manual Deployment (One-time Setup)

For the initial deployment, you may need to deploy manually:

```bash
# Navigate to infrastructure directory
cd infra/bicep

# Deploy to development
az deployment group create \
  --resource-group naughty-chats-dev-rg \
  --template-file main.bicep \
  --parameters @params/dev.parameters.json

# Deploy to production (when ready)
az deployment group create \
  --resource-group naughty-chats-prod-rg \
  --template-file main.bicep \
  --parameters @params/prod.parameters.json
```

## Automated Deployment

Once GitHub secrets are configured, deployments happen automatically:

1. **Development**: Deploys on every push to `main` branch
2. **Production**: Manual deployment via GitHub Actions workflow dispatch

### Triggering Production Deployment

1. Go to GitHub Actions tab
2. Select "Build and Deploy to Azure" workflow
3. Click "Run workflow"
4. Select "prod" environment
5. Click "Run workflow"

## Infrastructure Components

The deployment creates:

- **Azure Container Apps**: Hosts the FastAPI backend
- **Azure Cosmos DB**: Primary database for users, characters, chats
- **Azure Container Registry**: Stores Docker images
- **Azure Key Vault**: Manages secrets and keys
- **Azure Storage Account**: Stores generated images and files
- **Azure Service Bus**: Handles async job queues
- **Azure Front Door**: CDN, WAF, and HTTPS termination
- **Azure Log Analytics**: Centralized logging and monitoring

## Post-Deployment Configuration

After deployment, you'll need to:

1. **Configure Custom Domain** (Production only):
   ```bash
   # Add custom domain to Front Door
   az afd custom-domain create --profile-name your-frontdoor-profile \
     --resource-group naughty-chats-prod-rg \
     --custom-domain-name api-domain \
     --host-name api.naughtychats.com
   ```

2. **Populate Key Vault Secrets**:
   ```bash
   # Add required secrets to Key Vault
   az keyvault secret set --vault-name your-keyvault-name --name "jwt-secret" --value "your-secure-jwt-secret"
   az keyvault secret set --vault-name your-keyvault-name --name "stripe-secret-key" --value "sk_live_your-stripe-key"
   az keyvault secret set --vault-name your-keyvault-name --name "runpod-api-key" --value "your-runpod-key"
   ```

3. **Configure Managed Identity Permissions**:
   ```bash
   # Grant Container App access to Key Vault
   az keyvault set-policy --name your-keyvault-name \
     --object-id $(az containerapp show --name naughtychats-backend --resource-group naughty-chats-prod-rg --query identity.principalId -o tsv) \
     --secret-permissions get list
   ```

## Monitoring and Observability

- **Application Insights**: Monitor application performance and errors
- **Log Analytics**: Centralized logging from all components  
- **Azure Monitor**: Set up alerts for critical metrics
- **Front Door Analytics**: Monitor CDN performance and security

## Scaling Configuration

The infrastructure is configured for auto-scaling:

- **Development**: 1-3 replicas based on CPU/memory
- **Production**: 2-10 replicas based on HTTP requests and resource usage

## Security Features

- **WAF**: Web Application Firewall with OWASP rules
- **Private Endpoints**: Database and storage not publicly accessible
- **Managed Identity**: No stored credentials in application code
- **HTTPS Only**: All traffic encrypted in transit
- **Key Vault**: Centralized secret management

## Troubleshooting

### Common Issues

1. **Container App not starting**: Check environment variables and Key Vault access
2. **Database connection errors**: Verify Cosmos DB endpoint and firewall rules
3. **Image pull errors**: Check ACR permissions and image tags
4. **Front Door routing issues**: Verify origin health and routing rules

### Debugging Commands

```bash
# Check Container App logs
az containerapp logs show --name naughtychats-backend --resource-group naughty-chats-dev-rg

# Check deployment status
az deployment group show --name main --resource-group naughty-chats-dev-rg

# Test application endpoint
curl -k https://your-containerapp-url.azurecontainerapps.io/
```

## Cost Optimization

- **Container Apps**: Use consumption billing model for variable workloads
- **Cosmos DB**: Configure autoscale RU/s with appropriate limits
- **Storage**: Use cool tier for infrequently accessed images
- **Front Door**: Monitor bandwidth usage and optimize caching rules

## Backup and Disaster Recovery

- **Cosmos DB**: Continuous backup enabled with 30-day retention
- **Storage Account**: Geo-redundant storage for generated images
- **Key Vault**: Soft delete enabled with 90-day retention
- **Infrastructure**: All infrastructure defined as code for quick recreation