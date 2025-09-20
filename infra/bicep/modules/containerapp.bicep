@description('Container Apps environment and app for backend')
param location string
param appName string = 'naughtychats-backend'
param image string
param registryLoginServer string
param registryResourceId string

resource containerEnv 'Microsoft.Web/kubeEnvironments@2022-03-01' = {
  name: 'naughtychats-env-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {}
}

resource containerApp 'Microsoft.Web/containerApps@2022-03-01' = {
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
        }
      ]
    }
    template: {
      containers: [
        {
          name: appName
          image: image
          resources: {
            cpu: 0.5
            memory: '1Gi'
          }
        }
      ]
    }
  }
}

// Minimal role assignment placeholder (requires proper principalId resolution after deployment)
output containerAppName string = containerApp.name
output containerAppId string = containerApp.id
