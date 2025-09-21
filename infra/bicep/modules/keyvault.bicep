@description('Key Vault module skeleton')
param location string
param env string = 'dev'
param vaultName string = toLower('nchkv${substring(uniqueString(resourceGroup().id), 0, 6)}')

resource keyVault 'Microsoft.KeyVault/vaults@2021-06-01-preview' = {
  name: vaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
  }
}

output keyVaultName string = keyVault.name
