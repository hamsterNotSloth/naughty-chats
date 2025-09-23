@description('Container Apps environment and app for backend')
param location string
param environment string = 'dev'
param appName string = 'naughtychats-backend'
param image string
param registryLoginServer string
param keyVaultName string
param cosmosEndpoint string
param serviceBusNamespace string

// Container Apps Environment
resource containerEnv 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: 'naughtychats-env-${environment}-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: 'naughtychats-logs-${environment}-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container App with Managed Identity
resource containerApp 'Microsoft.App/containerApps@2022-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      registries: [
        {
          server: registryLoginServer
          identity: resourceId('Microsoft.ManagedIdentity/userAssignedIdentities', 'acr-identity')
        }
      ]
      secrets: [
        {
          name: 'cosmos-key'
          keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/cosmos-key'
          identity: containerApp.identity.principalId
        }
        {
          name: 'jwt-secret'
          keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/jwt-secret'
          identity: containerApp.identity.principalId
        }
      ]
    }
    template: {
      containers: [
        {
          name: appName
          image: image
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'ENV'
              value: environment
            }
            {
              name: 'COSMOS_URL'
              value: cosmosEndpoint
            }
            {
              name: 'COSMOS_KEY'
              secretRef: 'cosmos-key'
            }
            {
              name: 'COSMOS_DB'
              value: 'naughtychats-db'
            }
            {
              name: 'JWT_SECRET'
              secretRef: 'jwt-secret'
            }
            {
              name: 'CORS_ORIGINS'
              value: environment == 'prod' ? 'https://app.naughtychats.com' : 'http://localhost:3000,https://naughty-frontend-dev-ysurana.eastus.azurecontainer.io'
            }
            {
              name: 'SERVICE_BUS_NAMESPACE'
              value: serviceBusNamespace
            }
          ]
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/'
                port: 8080
              }
              initialDelaySeconds: 30
              periodSeconds: 10
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/'
                port: 8080
              }
              initialDelaySeconds: 5
              periodSeconds: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: environment == 'prod' ? 2 : 1
        maxReplicas: environment == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Output values
output containerAppName string = containerApp.name
output containerAppId string = containerApp.id
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
