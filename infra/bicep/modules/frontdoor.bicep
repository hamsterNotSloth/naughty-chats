@description('Front Door skeleton')
param location string
param env string = 'dev'

// Placeholder Front Door configuration - replace with production-ready rules, WAF policies and custom domains
resource frontDoor 'Microsoft.Network/frontDoors@2021-08-01' = {
  name: 'naughtychats-frontdoor-${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    routingRules: []
    backendPools: []
  }
}

output frontDoorName string = frontDoor.name
