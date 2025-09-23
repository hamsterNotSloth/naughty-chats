@description('Azure Front Door with WAF for secure HTTPS termination')
param location string = 'Global'
param environment string = 'dev'
param backendFqdn string
param customDomain string = ''

var frontDoorName = 'naughtychats-fd-${environment}-${uniqueString(resourceGroup().id)}'
var backendPoolName = 'naughtychats-backend-pool'
var routingRuleName = 'naughtychats-routing-rule'

// WAF Policy for security
resource wafPolicy 'Microsoft.Network/frontDoorWebApplicationFirewallPolicies@2022-05-01' = {
  name: 'naughtychats-waf-${environment}'
  location: location
  properties: {
    policySettings: {
      enabledState: 'Enabled'
      mode: 'Prevention'
      redirectUrl: 'https://www.example.com/blocked'
      customBlockResponseStatusCode: 403
      customBlockResponseBody: 'Request blocked by WAF'
    }
    managedRules: {
      managedRuleSets: [
        {
          ruleSetType: 'Microsoft_DefaultRuleSet'
          ruleSetVersion: '2.1'
          ruleGroupOverrides: []
        }
        {
          ruleSetType: 'Microsoft_BotManagerRuleSet'
          ruleSetVersion: '1.0'
          ruleGroupOverrides: []
        }
      ]
    }
    customRules: {
      rules: [
        {
          name: 'RateLimitRule'
          priority: 1
          enabledState: 'Enabled'
          ruleType: 'RateLimitRule'
          rateLimitDurationInMinutes: 1
          rateLimitThreshold: 100
          matchConditions: [
            {
              matchVariable: 'RequestUri'
              operator: 'Contains'
              matchValue: [
                '/api/'
              ]
            }
          ]
          action: 'Block'
        }
        {
          name: 'BlockSuspiciousUserAgents'
          priority: 2
          enabledState: 'Enabled'
          ruleType: 'MatchRule'
          matchConditions: [
            {
              matchVariable: 'RequestHeader'
              selector: 'User-Agent'
              operator: 'Contains'
              matchValue: [
                'bot'
                'crawler'
                'spider'
              ]
            }
          ]
          action: 'Block'
        }
      ]
    }
  }
}

// Front Door Profile (Standard tier for WAF support)
resource frontDoorProfile 'Microsoft.Cdn/profiles@2021-12-01' = {
  name: frontDoorName
  location: location
  sku: {
    name: 'Standard_AzureFrontDoor'
  }
  properties: {}
}

// Origin Group
resource originGroup 'Microsoft.Cdn/profiles/originGroups@2021-12-01' = {
  parent: frontDoorProfile
  name: backendPoolName
  properties: {
    loadBalancingSettings: {
      sampleSize: 4
      successfulSamplesRequired: 3
      additionalLatencyInMilliseconds: 50
    }
    healthProbeSettings: {
      probePath: '/'
      probeRequestType: 'HEAD'
      probeProtocol: 'Https'
      probeIntervalInSeconds: 60
    }
  }
}

// Origin
resource origin 'Microsoft.Cdn/profiles/originGroups/origins@2021-12-01' = {
  parent: originGroup
  name: 'backend-origin'
  properties: {
    hostName: backendFqdn
    httpPort: 80
    httpsPort: 443
    originHostHeader: backendFqdn
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
  }
}

// Endpoint
resource endpoint 'Microsoft.Cdn/profiles/afdEndpoints@2021-12-01' = {
  parent: frontDoorProfile
  name: 'naughtychats-endpoint-${environment}'
  location: location
  properties: {
    enabledState: 'Enabled'
  }
}

// Route for API traffic
resource apiRoute 'Microsoft.Cdn/profiles/afdEndpoints/routes@2021-12-01' = {
  parent: endpoint
  name: 'api-route'
  properties: {
    customDomains: customDomain != '' ? [
      {
        id: resourceId('Microsoft.Cdn/profiles/customDomains', frontDoorProfile.name, 'custom-domain')
      }
    ] : []
    originGroup: {
      id: originGroup.id
    }
    supportedProtocols: [
      'Http'
      'Https'
    ]
    patternsToMatch: [
      '/api/*'
      '/*'
    ]
    forwardingProtocol: 'HttpsOnly'
    linkToDefaultDomain: 'Enabled'
    httpsRedirect: 'Enabled'
  }
  dependsOn: [
    origin
  ]
}

// Security Policy to link WAF with endpoint
resource securityPolicy 'Microsoft.Cdn/profiles/securityPolicies@2021-12-01' = {
  parent: frontDoorProfile
  name: 'security-policy'
  properties: {
    parameters: {
      type: 'WebApplicationFirewall'
      wafPolicy: {
        id: wafPolicy.id
      }
      associations: [
        {
          domains: [
            {
              id: endpoint.id
            }
          ]
          patternsToMatch: [
            '/*'
          ]
        }
      ]
    }
  }
}

// Custom Domain (if provided)
resource customDomainResource 'Microsoft.Cdn/profiles/customDomains@2021-12-01' = if (customDomain != '') {
  parent: frontDoorProfile
  name: 'custom-domain'
  properties: {
    hostName: customDomain
    tlsSettings: {
      certificateType: 'ManagedCertificate'
      minimumTlsVersion: 'TLS12'
    }
  }
}

output frontDoorEndpointFqdn string = endpoint.properties.hostName
output frontDoorId string = frontDoorProfile.id
output wafPolicyId string = wafPolicy.id
