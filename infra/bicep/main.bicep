@description('Main deployment template for Naughty Chats infrastructure')
param location string = resourceGroup().location
param environment string = 'dev'
param appImage string = ''
param customDomain string = ''

// Create all core infrastructure modules
module cosmos 'modules/cosmosdb.bicep' = {
  name: 'cosmos-deployment'
  params: {
    location: location
    env: environment
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr-deployment'
  params: {
    location: location
    env: environment
  }
}

module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault-deployment'
  params: {
    location: location
    env: environment
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  params: {
    location: location
    env: environment
  }
}

module servicebus 'modules/servicebus.bicep' = {
  name: 'servicebus-deployment'
  params: {
    location: location
    env: environment
  }
}

// Deploy Container Apps after dependencies are ready
module containerapp 'modules/containerapp.bicep' = {
  name: 'containerapp-deployment'
  params: {
    location: location
    environment: environment
    image: appImage != '' ? appImage : '${acr.outputs.loginServer}/naughtychats-backend:latest'
    registryLoginServer: acr.outputs.loginServer
    keyVaultName: keyvault.outputs.keyVaultName
    cosmosEndpoint: cosmos.outputs.accountEndpoint
    serviceBusNamespace: servicebus.outputs.namespaceName
  }
  dependsOn: [
    cosmos
    acr
    keyvault
    servicebus
  ]
}

// Deploy Front Door for HTTPS termination
module frontdoor 'modules/frontdoor.bicep' = {
  name: 'frontdoor-deployment'
  params: {
    environment: environment
    backendFqdn: replace(containerapp.outputs.containerAppUrl, 'https://', '')
    customDomain: customDomain
  }
  dependsOn: [
    containerapp
  ]
}

// Outputs for reference
output cosmosEndpoint string = cosmos.outputs.accountEndpoint
output acrLoginServer string = acr.outputs.loginServer
output keyVaultName string = keyvault.outputs.keyVaultName
output containerAppUrl string = containerapp.outputs.containerAppUrl
output frontDoorUrl string = 'https://${frontdoor.outputs.frontDoorEndpointFqdn}'
output storageAccountName string = storage.outputs.storageAccountName
output serviceBusNamespace string = servicebus.outputs.namespaceName

