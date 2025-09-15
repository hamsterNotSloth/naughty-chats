#!/usr/bin/env bash

# Manual deployment script for naughty-chats (FastAPI backend + Next.js frontend)
# This script provisions Azure resources and deploys container apps WITHOUT GitHub Actions.
# Prereqs: az CLI, docker (or use ACR remote builds), logged in via `az login`.

set -euo pipefail

### --------------------------- USER CONFIGURABLE SECTION ---------------------------
# Adjust these names if you want different resource naming. Keep them globally unique where needed.
RG="nchats-prod"
LOCATION="eastus"
ACR_NAME="nchatsacr"               # must be globally unique
LOG_WS="nchats-law"
CAE_ENV="nchats-ca-env"
BACKEND_APP="nchats-backend"
FRONTEND_APP="nchats-frontend"
COSMOS_ACCOUNT="nchats-cosmos"     # must be globally unique
COSMOS_DB="nchatsdb"
COSMOS_USERS_CONTAINER="users"
COSMOS_CHARACTERS_CONTAINER="characters"

# Optional: SKU choices / sizing (tweak as needed)
# Cosmos throughput baseline (autoscale/manual). Using RU based containers.
COSMOS_THROUGHPUT=400

### --------------------------- SECRETS INPUT --------------------------------------
# Provide SECRET_KEY and Postgres admin password securely BEFORE running or interactively.
# NEVER commit real values to source control.

SECRET_KEY="${SECRET_KEY:-}"
COSMOS_KEY="${COSMOS_KEY:-}"

if [[ -z "$SECRET_KEY" ]]; then
  read -r -p "Enter (or paste) SECRET_KEY (leave blank to auto-generate): " SECRET_KEY_INPUT || true
  if [[ -z "$SECRET_KEY_INPUT" ]]; then
    SECRET_KEY=$(python -c 'import secrets;print(secrets.token_urlsafe(48))')
    echo "Generated SECRET_KEY (length: ${#SECRET_KEY})"
  else
    SECRET_KEY="$SECRET_KEY_INPUT"
  fi
fi

if [[ -z "$COSMOS_KEY" ]]; then
  echo "COSMOS_KEY will be retrieved after account creation (primary master key)."
fi

echo "\nResource Group: $RG"
echo "Location:       $LOCATION"
echo "ACR:            $ACR_NAME"
echo "Cosmos Account: $COSMOS_ACCOUNT (db: $COSMOS_DB)"
echo "Container Env:  $CAE_ENV"
echo "Backend App:    $BACKEND_APP"
echo "Frontend App:   $FRONTEND_APP"
echo "\nProceed in 5s (Ctrl+C to abort)..."; sleep 5

### --------------------------- VALIDATION -----------------------------------------
command -v az >/dev/null || { echo "az CLI not found"; exit 1; }
command -v docker >/dev/null || echo "WARNING: docker not found, will attempt remote ACR build if needed" >&2

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Using subscription: $SUBSCRIPTION_ID"

### --------------------------- RESOURCE GROUP & ACR -------------------------------
echo "[1/8] Creating resource group if missing..."
az group create --name "$RG" --location "$LOCATION" >/dev/null

echo "[2/8] Creating / ensuring ACR..."
if ! az acr show -n "$ACR_NAME" -g "$RG" >/dev/null 2>&1; then
  az acr create --resource-group "$RG" --name "$ACR_NAME" --sku Basic
else
  echo "ACR $ACR_NAME already exists"
fi

### --------------------------- LOG ANALYTICS & ENV --------------------------------
echo "[3/8] Creating / ensuring Log Analytics workspace..."
if ! az monitor log-analytics workspace show -g "$RG" -n "$LOG_WS" >/dev/null 2>&1; then
  az monitor log-analytics workspace create --workspace-name "$LOG_WS" --resource-group "$RG" --location "$LOCATION"
fi
az monitor log-analytics workspace update --resource-group "$RG" --workspace-name "$LOG_WS" --retention-time 30 >/dev/null

LOG_ID=$(az monitor log-analytics workspace show -g "$RG" -n "$LOG_WS" --query customerId -o tsv)
LOG_KEY=$(az monitor log-analytics workspace get-shared-keys -g "$RG" -n "$LOG_WS" --query primarySharedKey -o tsv)

echo "[4/8] Creating / ensuring Container Apps environment..."
if ! az containerapp env show -g "$RG" -n "$CAE_ENV" >/dev/null 2>&1; then
  az containerapp env create --name "$CAE_ENV" --resource-group "$RG" --location "$LOCATION" \
    --logs-workspace-id "$LOG_ID" --logs-workspace-key "$LOG_KEY"
else
  echo "Container Apps env $CAE_ENV already exists"
fi

### --------------------------- POSTGRES -------------------------------------------
echo "[5/8] Creating / ensuring Cosmos DB Account..."
if ! az cosmosdb show -g "$RG" -n "$COSMOS_ACCOUNT" >/dev/null 2>&1; then
  az cosmosdb create -g "$RG" -n "$COSMOS_ACCOUNT" --default-consistency-level Session
else
  echo "Cosmos account $COSMOS_ACCOUNT already exists"
fi

echo "[5/8b] Creating / ensuring Cosmos SQL database & containers..."
if ! az cosmosdb sql database show -g "$RG" -a "$COSMOS_ACCOUNT" -n "$COSMOS_DB" >/dev/null 2>&1; then
  az cosmosdb sql database create -g "$RG" -a "$COSMOS_ACCOUNT" -n "$COSMOS_DB"
fi
if ! az cosmosdb sql container show -g "$RG" -a "$COSMOS_ACCOUNT" -d "$COSMOS_DB" -n "$COSMOS_USERS_CONTAINER" >/dev/null 2>&1; then
  az cosmosdb sql container create -g "$RG" -a "$COSMOS_ACCOUNT" -d "$COSMOS_DB" -n "$COSMOS_USERS_CONTAINER" --partition-key-path /id --throughput $COSMOS_THROUGHPUT
fi
if ! az cosmosdb sql container show -g "$RG" -a "$COSMOS_ACCOUNT" -d "$COSMOS_DB" -n "$COSMOS_CHARACTERS_CONTAINER" >/dev/null 2>&1; then
  az cosmosdb sql container create -g "$RG" -a "$COSMOS_ACCOUNT" -d "$COSMOS_DB" -n "$COSMOS_CHARACTERS_CONTAINER" --partition-key-path /id --throughput $COSMOS_THROUGHPUT
fi

COSMOS_ENDPOINT=$(az cosmosdb show -g "$RG" -n "$COSMOS_ACCOUNT" --query documentEndpoint -o tsv)
COSMOS_KEY=$(az cosmosdb keys list -g "$RG" -n "$COSMOS_ACCOUNT" --type keys --query primaryMasterKey -o tsv)

### --------------------------- BUILD / PUSH IMAGES --------------------------------
echo "[6/8] Building & pushing images..."
if command -v docker >/dev/null; then
  az acr login --name "$ACR_NAME"
  docker build -t "$ACR_NAME.azurecr.io/backend:latest" -f backend/Dockerfile .
  docker push "$ACR_NAME.azurecr.io/backend:latest"
  docker build -t "$ACR_NAME.azurecr.io/frontend:latest" -f frontend/Dockerfile .
  docker push "$ACR_NAME.azurecr.io/frontend:latest"
else
  echo "Docker not installed; using remote ACR build"
  az acr build -r "$ACR_NAME" -t backend:latest -f backend/Dockerfile .
  az acr build -r "$ACR_NAME" -t frontend:latest -f frontend/Dockerfile .
fi

ACR_PASSWORD=$(az acr credential show -n "$ACR_NAME" --query passwords[0].value -o tsv)

### --------------------------- CONTAINER APPS -------------------------------------
echo "[7/8] Creating / updating backend container app..."
if ! az containerapp show -n "$BACKEND_APP" -g "$RG" >/dev/null 2>&1; then
  az containerapp create \
    --name "$BACKEND_APP" --resource-group "$RG" --environment "$CAE_ENV" \
    --image "$ACR_NAME.azurecr.io/backend:latest" --target-port 8000 --ingress external \
    --registry-server "$ACR_NAME.azurecr.io" --registry-username "$ACR_NAME" --registry-password "$ACR_PASSWORD" \
  --secrets secret-key="$SECRET_KEY" cosmos-endpoint="$COSMOS_ENDPOINT" cosmos-key="$COSMOS_KEY" \
  --env-vars SECRET_KEY=secretref:secret-key COSMOS_ENDPOINT=secretref:cosmos-endpoint COSMOS_KEY=secretref:cosmos-key COSMOS_DATABASE="$COSMOS_DB" COSMOS_USERS_CONTAINER="$COSMOS_USERS_CONTAINER" COSMOS_CHARACTERS_CONTAINER="$COSMOS_CHARACTERS_CONTAINER" ALLOWED_ORIGINS="*" LOCAL_AUTH_ENABLED="true"
else
  echo "Updating backend image and env vars..."
  az containerapp update -n "$BACKEND_APP" -g "$RG" --image "$ACR_NAME.azurecr.io/backend:latest" \
    --set-env-vars ALLOWED_ORIGINS="*" LOCAL_AUTH_ENABLED="true" COSMOS_DATABASE="$COSMOS_DB" COSMOS_USERS_CONTAINER="$COSMOS_USERS_CONTAINER" COSMOS_CHARACTERS_CONTAINER="$COSMOS_CHARACTERS_CONTAINER"
  az containerapp secret set -n "$BACKEND_APP" -g "$RG" --secrets secret-key="$SECRET_KEY" cosmos-endpoint="$COSMOS_ENDPOINT" cosmos-key="$COSMOS_KEY"
fi

BACKEND_URL=$(az containerapp show -n "$BACKEND_APP" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)
echo "Backend FQDN: https://$BACKEND_URL"

echo "[8/8] Creating / updating frontend container app..."
if ! az containerapp show -n "$FRONTEND_APP" -g "$RG" >/dev/null 2>&1; then
  az containerapp create \
    --name "$FRONTEND_APP" --resource-group "$RG" --environment "$CAE_ENV" \
    --image "$ACR_NAME.azurecr.io/frontend:latest" --target-port 3000 --ingress external \
    --registry-server "$ACR_NAME.azurecr.io" --registry-username "$ACR_NAME" --registry-password "$ACR_PASSWORD" \
    --env-vars NEXT_PUBLIC_API_BASE_URL="https://$BACKEND_URL"
else
  echo "Updating frontend image and API base URL..."
  az containerapp update -n "$FRONTEND_APP" -g "$RG" --image "$ACR_NAME.azurecr.io/frontend:latest" \
    --set-env-vars NEXT_PUBLIC_API_BASE_URL="https://$BACKEND_URL"
fi

FRONTEND_URL=$(az containerapp show -n "$FRONTEND_APP" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)
echo "Frontend FQDN: https://$FRONTEND_URL"

echo "\nDeployment complete. Basic health check:" 
curl -fsS "https://$BACKEND_URL/healthz" || echo "Health endpoint failed (may still be starting)"

cat <<EOF

Next steps:
  - Visit frontend: https://$FRONTEND_URL
  - Secure improvements: managed identity + Key Vault, tighten CORS, enforce Entra auth.
  - Rotate secrets by: az containerapp secret set ... then az containerapp update ...

EOF
