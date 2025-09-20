@description('Service Bus module skeleton')
param location string
param env string = 'dev'
param namespaceName string = 'naughtychatssb${env}${uniqueString(resourceGroup().id)}'

resource sbNamespace 'Microsoft.ServiceBus/namespaces@2021-11-01' = {
  name: namespaceName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {}
}

resource genQueue 'Microsoft.ServiceBus/namespaces/queues@2021-11-01' = {
  parent: sbNamespace
  name: 'gen-jobs'
  properties: {
    enablePartitioning: false
    lockDuration: 'PT1M'
  }
}

output namespaceName string = sbNamespace.name
output queueName string = genQueue.name
