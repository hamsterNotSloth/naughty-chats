@description('Location for all resources')
param location string = resourceGroup().location
param environment string = 'dev'

// Example composition of modules. Fill parameters as needed for your environment.
module cosmos 'modules/cosmosdb.bicep' = {
  name: 'cosmos'
  params: {
    location: location
    env: environment
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    location: location
    env: environment
  }
}

module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    env: environment
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    env: environment
  }
}

module servicebus 'modules/servicebus.bicep' = {
  name: 'servicebus'
  params: {
    location: location
    env: environment
  }
}

