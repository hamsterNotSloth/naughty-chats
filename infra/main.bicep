@description('Project name prefix (e.g. nchat)')
param prefix string
@description('Environment name (e.g. dev, prod)')
param environment string = 'dev'
@description('Azure region')
param location string = resourceGroup().location

@description('Cosmos DB account name (unique)')
param cosmosAccountName string = 'cosmos-${prefix}-${environment}'
@description('Cosmos DB database name')
param cosmosDbName string = 'nchatsdb'
@description('Users container throughput (RU)')
param usersThroughput int = 400
@description('Characters container throughput (RU)')
param charactersThroughput int = 400

@description('Log Analytics workspace name')
param logName string = 'law-${prefix}-${environment}'
@description('Container Apps Environment name')
param caeName string = 'cae-${prefix}-${environment}'
@description('Azure Container Registry name (no dashes)')
param acrName string

@description('Backend Entra API audience (api://APP_ID)')
param entraApiAudience string
@description('Entra Tenant Id (GUID)')
param entraTenantId string
@description('Optional B2C policy')
param entraB2cPolicy string = ''
@description('Optional B2C tenant primary domain')
param entraB2cPrimaryDomain string = ''

@description('Frontend client id')
param spaClientId string
@description('Frontend API scope (api://APP_ID/.default)')
param spaApiScope string

@description('Allowed origins for CORS (comma separated)')
param allowedOrigins string

@description('API container image (repository:tag). Defaults to placeholder until pipeline updates revision.')
param apiImage string = 'mcr.microsoft.com/oss/nginx/nginx:1.25.3'
@description('Web container image (repository:tag). Defaults to placeholder until pipeline updates revision.')
param webImage string = 'mcr.microsoft.com/azuredocs/aks-helloworld:v1'

// Resource names
var apiAppName = 'ca-${prefix}-api-${environment}'
var webAppName = 'ca-${prefix}-web-${environment}'

// Log Analytics
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

// Container Apps Environment
resource containerEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: caeName
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

// ACR
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {}
}

// Cosmos DB account
resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    disableKeyBasedMetadataWriteAccess: false
  }
}

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  name: cosmosDbName
  parent: cosmos
  properties: {
    resource: {
      id: cosmosDbName
    }
  }
}

resource usersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  name: 'users'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'users'
      partitionKey: {
        paths: [ '/id' ]
        kind: 'Hash'
      }
    }
    options: {
      throughput: usersThroughput
    }
  }
}

resource charactersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  name: 'characters'
  parent: cosmosDb
  properties: {
    resource: {
      id: 'characters'
      partitionKey: {
        paths: [ '/id' ]
        kind: 'Hash'
      }
    }
    options: {
      throughput: charactersThroughput
    }
  }
}

// Container Apps - API
resource apiApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: apiAppName
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: '${acr.name}.azurecr.io'
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-pwd'
        }
      ]
      secrets: [
        {
          name: 'acr-pwd'
          value: acr.listCredentials().passwords[0].value
        }
        {
          name: 'cosmos-endpoint'
          value: cosmos.properties.documentEndpoint
        }
        {
          name: 'cosmos-key'
          value: cosmos.listKeys().primaryMasterKey
        }
      ]
      activeRevisionsMode: 'single'
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          env: [
            { name: 'COSMOS_ENDPOINT', value: 'secretref:cosmos-endpoint' }
            { name: 'COSMOS_KEY', value: 'secretref:cosmos-key' }
            { name: 'COSMOS_DATABASE', value: cosmosDbName }
            { name: 'COSMOS_USERS_CONTAINER', value: 'users' }
            { name: 'COSMOS_CHARACTERS_CONTAINER', value: 'characters' }
            { name: 'COSMOS_AUTO_PROVISION', value: 'false' }
            { name: 'ALLOWED_ORIGINS', value: allowedOrigins }
            { name: 'ENTRA_API_AUDIENCE', value: entraApiAudience }
            { name: 'ENTRA_TENANT_ID', value: entraTenantId }
            { name: 'ENTRA_B2C_POLICY', value: entraB2cPolicy }
            { name: 'ENTRA_B2C_TENANT_PRIMARY_DOMAIN', value: entraB2cPrimaryDomain }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// Container Apps - Web
resource webApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: webAppName
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'auto'
      }
      registries: [
        {
            server: '${acr.name}.azurecr.io'
            username: acr.listCredentials().username
            passwordSecretRef: 'acr-pwd'
        }
      ]
      secrets: [
        {
          name: 'acr-pwd'
          value: acr.listCredentials().passwords[0].value
        }
      ]
      activeRevisionsMode: 'single'
    }
    template: {
      containers: [
        {
          name: 'web'
          image: webImage
          env: [
            { name: 'NEXT_PUBLIC_ENTRA_CLIENT_ID', value: spaClientId }
            { name: 'NEXT_PUBLIC_ENTRA_API_SCOPE', value: spaApiScope }
            { name: 'NEXT_PUBLIC_ENTRA_TENANT_ID', value: entraTenantId }
            { name: 'NEXT_PUBLIC_B2C_TENANT_NAME', value: toLower(replace(entraB2cPrimaryDomain, '.onmicrosoft.com', '')) }
            { name: 'NEXT_PUBLIC_B2C_USER_FLOW', value: entraB2cPolicy }
            { name: 'NEXT_PUBLIC_API_BASE_URL', value: 'https://${apiApp.properties.configuration.ingress.fqdn}' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output apiFqdn string = apiApp.properties.configuration.ingress.fqdn
output webFqdn string = webApp.properties.configuration.ingress.fqdn
output cosmosEndpoint string = cosmos.properties.documentEndpoint
