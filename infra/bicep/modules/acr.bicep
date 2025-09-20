@description('ACR module skeleton')
param location string
param env string = 'dev'
param registryName string = 'naughtychatsacr${uniqueString(resourceGroup().id)}'

resource acr 'Microsoft.ContainerRegistry/registries@2021-09-01' = {
  name: registryName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: true
  }
}

output registryName string = acr.name
output loginServer string = acr.properties.loginServer
