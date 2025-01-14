targetScope = 'subscription'

// === PARAMETERS ===
// ===A
param acaIdentityName string = deploymentTarget == 'containerapps' ? '${environmentName}-aca-identity' : ''
param acaManagedEnvironmentName string = deploymentTarget == 'containerapps' ? '${environmentName}-aca-env' : ''
param allowedOrigin string = '' // Used for optional CORS support for alternate frontends
param applicationInsightsDashboardName string = ''
param applicationInsightsName string = ''
param appServicePlanName string = ''
param appServiceSkuName string
param authTenantId string = ''
param azureContainerAppsWorkloadProfile string
@secure()
param azureOpenAiApiKey string = ''
param azureOpenAiApiVersion string = ''
param azureOpenAiCustomUrl string = ''
// ===B
param backendServiceName string = ''
// ===C
param clientAppId string = ''
@secure()
param clientAppSecret string = ''
param computerVisionResourceGroupName string = ''
param computerVisionResourceGroupLocation string = ''
param computerVisionServiceName string = ''
param computerVisionSkuName string
param containerRegistryName string = deploymentTarget == 'containerapps'
  ? '${replace(environmentName, '-', '')}acr'
  : ''
// ===D
param deployAzureOpenAi bool = openAiHost == 'azure'
@allowed(['appservice', 'containerapps'])
param deploymentTarget string = 'appservice'
param disableAppServicesAuthentication bool = false // Force using MSAL app authentication instead of built-in App Service authentication
@description('Location for the Document Intelligence resource group')
@allowed(['eastus', 'westus2', 'westeurope'])
@metadata({
  azd: {
    type: 'location'
  }
})
param documentIntelligenceResourceGroupLocation string
param documentIntelligenceResourceGroupName string = ''
param documentIntelligenceServiceName string = ''
param documentIntelligenceSkuName string
// ===E
param embeddingDeploymentCapacity int = 0
param embeddingDeploymentName string = ''
param embeddingDeploymentVersion string = ''
param embeddingDimensions int = 0
param embeddingModelName string = ''
param enableGlobalDocuments bool = false // To allow authenticated users to search on documents that have no access controls assigned, even when access control is required
@description('Enable language picker')
param enableLanguagePicker bool = false
param enableUnauthenticatedAccess bool = false
param enforceAccessControl bool = false
@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string
// ===F+
// ===G
param gpt35DeploymentCapacity int = 30
param gpt35DeploymentName string = 'opensourcerer-completions-35t'
param gpt35DeploymentVersion string = '0613'
param gpt35ModelName string = 'gpt-35-turbo'
param gpt4DeploymentCapacity int = 50
param gpt4DeploymentName string = 'opensourcerer-completions-4o'
param gpt4ModelName string = 'gpt-4o'
param gpt4ModelVersion string = '2024-05-13'
param gpt4vDeploymentCapacity int = 10
param gpt4vDeploymentName string = 'opensourcerer-completions-4V'
param gpt4vModelName string = 'gpt-4V'
param gpt4vModelVersion string = '2024-05-13'
// ===H
// ===I
@allowed(['None', 'AzureServices'])
@description('If allowedIp is set, whether azure services are allowed to bypass the storage and AI services firewall.')
param ipBypass string = 'AzureServices'
param isAzureOpenAiHost bool = startsWith(openAiHost, 'azure')
// ===J
// ===K
// ===L
@minLength(1)
@description('Primary location for all resources')
param location string
param logAnalyticsName string = ''
// ===O
@allowed(['azure', 'openai', 'azure_custom'])
param openAiHost string
@secure()
param openAiApiKey string = ''
param openAiApiOrganization string = ''
@description('Location for the OpenAI resource group')
@allowed([
  'canadaeast'
  'eastus'
  'eastus2'
  'westus'
  'westus2'
])
@metadata({
  azd: {
    type: 'location'
  }
})
param openAiResourceGroupLocation string
param openAiResourceGroupName string = ''
param openAiServiceName string = ''
param openAiSkuName string = 'S0'
// ===P
@description('Id of the user or app to assign application roles')
param principalId string = ''
@description('Public network access value for all deployed resources')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'
// ===R
param resourceGroupName string = ''
@description('Whether the deployment is running on Azure DevOps Pipeline')
param runInADO string = ''
@description('Whether the deployment is running on GitHub Actions')
param runInGIT string = ''
// ===S
param searchIndexName string
param searchQueryLanguage string
param searchQuerySpeller string
param searchServiceLocation string = ''
param searchServiceName string = ''
param searchServiceResourceGroupName string = ''
param searchServiceSemanticRankerLevel string
param searchServiceSkuName string = 'S0'
param serverAppId string = ''
@secure()
param serverAppSecret string = ''
param speechServiceLocation string = ''
param speechServiceName string = ''
param speechServiceResourceGroupName string = ''
param speechServiceSkuName string
param storageAccountName string = ''
param storageContainerName string = 'content'
param storageResourceGroupLocation string = location
param storageResourceGroupName string = ''
param storageSkuName string
// ===T
param tenantId string = tenant().tenantId
// ===U
param useAuthentication bool = false
param useGPT4V bool = false
param useGPT4 bool = true
@description('Use Application Insights for monitoring and performance tracing')
param useApplicationInsights bool = false
@description('Add a private endpoints for network connectivity')
param usePrivateEndpoint bool = false
param userStorageAccountName string = ''
param userStorageContainerName string = 'user-content'
@description('Use speech recognition feature in browser')
param useSpeechInputBrowser bool = false
@description('Use speech synthesis in browser')
param useSpeechOutputBrowser bool = false
@description('Use Azure speech service for reading out text')
param useSpeechOutputAzure bool = false
@description('Use chat history feature in browser')
param useChatHistoryBrowser bool = false
@description('Show options to use vector embeddings for searching in the app UI')
param useVectors bool = false
@description('Use Built-in integrated Vectorization feature of AI Search to vectorize and ingest documents')
param useIntegratedVectorization bool = true
@description('Enable user document upload feature')
param useUserUpload bool = false
param useLocalPdfParser bool = false
param useLocalHtmlParser bool = false
// ===W
@description('Used by azd for containerapps deployment')
param webAppExists bool

// === VARIABLES ===
var abbrs = loadJsonContent('abbreviations.json')
var actualSearchServiceSemanticRankerLevel = (searchServiceSkuName == 'free')
  ? 'disabled'
  : searchServiceSemanticRankerLevel
var appEnvVariables = {
  ALLOWED_ORIGIN: allowedOrigin
  APPLICATIONINSIGHTS_CONNECTION_STRING: useApplicationInsights
    ? monitoring.outputs.applicationInsightsConnectionString
    : ''
  AZURE_AUTHENTICATION_ISSUER_URI: authenticationIssuerUri
  AZURE_AUTH_TENANT_ID: tenantIdForAuth
  AZURE_CLIENT_APP_ID: clientAppId
  AZURE_CLIENT_APP_SECRET: clientAppSecret
  AZURE_DOCUMENTINTELLIGENCE_SERVICE: documentIntelligence.outputs.name
  AZURE_ENABLE_GLOBAL_DOCUMENT_ACCESS: enableGlobalDocuments
  AZURE_ENABLE_UNAUTHENTICATED_ACCESS: enableUnauthenticatedAccess
  AZURE_ENFORCE_ACCESS_CONTROL: enforceAccessControl
  // Shared by all OpenAI deployments
  AZURE_OPENAI_API_KEY_OVERRIDE: azureOpenAiApiKey
  AZURE_OPENAI_API_VERSION: azureOpenAiApiVersion
  AZURE_OPENAI_CHATGPT_DEPLOYMENT: chatGpt.deploymentName
  AZURE_OPENAI_CHATGPT_MODEL: chatGpt.modelName
  AZURE_OPENAI_CUSTOM_URL: azureOpenAiCustomUrl
  AZURE_OPENAI_EMB_DEPLOYMENT: embedding.deploymentName
  AZURE_OPENAI_EMB_DIMENSIONS: embedding.dimensions
  AZURE_OPENAI_EMB_MODEL_NAME: embedding.modelName
  AZURE_OPENAI_GPT4V_DEPLOYMENT: useGPT4V ? gpt4vDeploymentName : ''
  AZURE_OPENAI_GPT4V_MODEL: gpt4vModelName
  // Specific to Azure OpenAI
  AZURE_OPENAI_SERVICE: isAzureOpenAiHost && deployAzureOpenAi ? openAi.outputs.name : ''
  AZURE_SEARCH_INDEX: searchIndexName
  AZURE_SEARCH_QUERY_LANGUAGE: searchQueryLanguage
  AZURE_SEARCH_QUERY_SPELLER: searchQuerySpeller
  AZURE_SEARCH_SEMANTIC_RANKER: actualSearchServiceSemanticRankerLevel
  AZURE_SEARCH_SERVICE: searchService.outputs.name
  AZURE_SERVER_APP_ID: serverAppId
  AZURE_SERVER_APP_SECRET: serverAppSecret
  AZURE_SPEECH_SERVICE_ID: useSpeechOutputAzure ? speech.outputs.resourceId : ''
  AZURE_SPEECH_SERVICE_LOCATION: useSpeechOutputAzure ? speech.outputs.location : ''
  AZURE_STORAGE_ACCOUNT: storage.outputs.name
  AZURE_STORAGE_CONTAINER: storageContainerName
  AZURE_TENANT_ID: tenantId
  AZURE_USERSTORAGE_ACCOUNT: useUserUpload ? userStorage.outputs.name : ''
  AZURE_USERSTORAGE_CONTAINER: useUserUpload ? userStorageContainerName : ''
  AZURE_VISION_ENDPOINT: useGPT4V ? computerVision.outputs.endpoint : ''
  // CORS support, for frontends on other hosts
  ENABLE_LANGUAGE_PICKER: enableLanguagePicker
  OPENAI_API_KEY: openAiApiKey
  OPENAI_HOST: openAiHost
  OPENAI_ORGANIZATION: openAiApiOrganization
  // Optional login and document level access control system
  RUNNING_IN_PRODUCTION: 'true'
  USE_CHAT_HISTORY_BROWSER: useChatHistoryBrowser
  USE_GPT4: useGPT4
  USE_GPT4V: useGPT4V
  USE_LOCAL_HTML_PARSER: useLocalHtmlParser
  USE_LOCAL_PDF_PARSER: useLocalPdfParser
  USE_SPEECH_INPUT_BROWSER: useSpeechInputBrowser
  USE_SPEECH_OUTPUT_AZURE: useSpeechOutputAzure
  USE_SPEECH_OUTPUT_BROWSER: useSpeechOutputBrowser
  USE_VECTORS: useVectors
  SECRET_KEY: 'f1c4a3b5e6f789ab12cd34ef56g78901h234567890ab1234cd5678ef9012abcd'
  USERS: 'eyJhZG1pbl91c2VyIjp7InBhc3N3b3JkIjoiYWRtaW4xMjMiLCJyb2xlIjoiQWRtaW4ifSwicG93ZXJfdXNlciI6eyJwYXNzd29yZCI6InBvd2VyMTIzIiwicm9sZSI6IlBvd2VyIn0sImF1dGhfdXNlciI6eyJwYXNzd29yZCI6ImF1dGgxMjMiLCJyb2xlIjoiQXV0aCJ9fQ=='
}
var authenticationIssuerUri = '${environment().authentication.loginEndpoint}${tenantIdForAuth}/v2.0'
var chatGpt = {
  modelName: !useGPT4 ? gpt35ModelName : gpt4ModelName
  deploymentName: !useGPT4 ? gpt35DeploymentName : gpt4DeploymentName
  deploymentVersion: !useGPT4 ? gpt35DeploymentVersion : gpt4ModelVersion
  deploymentCapacity: !useGPT4 ? gpt35DeploymentCapacity : gpt4DeploymentCapacity
}
var defaultOpenAiDeployments = [
  {
    name: chatGpt.deploymentName
    model: {
      format: 'OpenAI'
      name: chatGpt.modelName
      version: chatGpt.deploymentVersion
    }
    sku: {
      name: 'Standard'
      capacity: chatGpt.deploymentCapacity
    }
  }
  {
    name: embedding.deploymentName
    model: {
      format: 'OpenAI'
      name: embedding.modelName
      version: embedding.deploymentVersion
    }
    sku: {
      name: 'Standard'
      capacity: embedding.deploymentCapacity
    }
  }
]
var embedding = {
  modelName: !empty(embeddingModelName) ? embeddingModelName : 'text-embedding-ada-002'
  deploymentName: !empty(embeddingDeploymentName) ? embeddingDeploymentName : 'opensourcerer-embeddings-002'
  deploymentVersion: !empty(embeddingDeploymentVersion) ? embeddingDeploymentVersion : '2'
  deploymentCapacity: embeddingDeploymentCapacity != 0 ? embeddingDeploymentCapacity : 50
  dimensions: embeddingDimensions != 0 ? embeddingDimensions : 1536
}
var environmentData = environment()
var openAiDeployments = concat(
  defaultOpenAiDeployments,
  useGPT4V
    ? [
        {
          name: gpt4vDeploymentName
          model: {
            format: 'OpenAI'
            name: gpt4vModelName
            version: gpt4vModelVersion
          }
          sku: {
            name: 'Standard'
            capacity: gpt4vDeploymentCapacity
          }
        }
      ]
    : []
)
var openAiPrivateEndpointConnection = (isAzureOpenAiHost && deployAzureOpenAi && deploymentTarget == 'appservice')
  ? [
      {
        groupId: 'account'
        dnsZoneName: 'privatelink.openai.azure.com'
        resourceIds: concat(
          [openAi.outputs.resourceId],
          useGPT4V ? [computerVision.outputs.resourceId] : [],
          !useLocalPdfParser ? [documentIntelligence.outputs.resourceId] : []
        )
      }
    ]
  : []
var otherPrivateEndpointConnections = (usePrivateEndpoint && deploymentTarget == 'appservice')
  ? [
      {
        groupId: 'blob'
        dnsZoneName: 'privatelink.blob.${environmentData.suffixes.storage}'
        resourceIds: concat([storage.outputs.id], useUserUpload ? [userStorage.outputs.id] : [])
      }
      {
        groupId: 'searchService'
        dnsZoneName: 'privatelink.search.windows.net'
        resourceIds: [searchService.outputs.id]
      }
      {
        groupId: 'sites'
        dnsZoneName: 'privatelink.azurewebsites.net'
        resourceIds: [backend.outputs.id]
      }
    ]
  : []  
var principalType = empty(runInGIT) && empty(runInADO) ? 'User' : 'ServicePrincipal'
var privateEndpointConnections = concat(otherPrivateEndpointConnections, openAiPrivateEndpointConnection)
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }
var tenantIdForAuth = !empty(authTenantId) ? authTenantId : tenantId

// === RESOURCES ===
resource computerVisionResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(computerVisionResourceGroupName)) {
  name: !empty(computerVisionResourceGroupName) ? computerVisionResourceGroupName : resourceGroup.name
}
resource documentIntelligenceResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(documentIntelligenceResourceGroupName)) {
  name: !empty(documentIntelligenceResourceGroupName) ? documentIntelligenceResourceGroupName : resourceGroup.name
}
resource openAiResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(openAiResourceGroupName)) {
  name: !empty(openAiResourceGroupName) ? openAiResourceGroupName : resourceGroup.name
}
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}
resource searchServiceResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(searchServiceResourceGroupName)) {
  name: !empty(searchServiceResourceGroupName) ? searchServiceResourceGroupName : resourceGroup.name
}
resource speechResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(speechServiceResourceGroupName)) {
  name: !empty(speechServiceResourceGroupName) ? speechServiceResourceGroupName : resourceGroup.name
}
resource storageResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(storageResourceGroupName)) {
  name: !empty(storageResourceGroupName) ? storageResourceGroupName : resourceGroup.name
}


// === MODULES ===

// === Application Hosting ===

// App Service Plan to group applications under the same payment plan and SKU
module appServicePlan 'core/host/appserviceplan.bicep' = if (deploymentTarget == 'appservice') {
  name: 'appserviceplan'
  scope: resourceGroup
  params: {
    name: !empty(appServicePlanName) ? appServicePlanName : '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: appServiceSkuName
      capacity: 1
    }
    kind: 'linux'
  }
}

// App Service for the web application (Python Quart app with JS frontend)
module backend 'core/host/appservice.bicep' = if (deploymentTarget == 'appservice') {
  name: 'web'
  scope: resourceGroup
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesAppService}backend-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'backend' })
    // Need to check deploymentTarget again due to https://github.com/Azure/bicep/issues/3990
    appServicePlanId: deploymentTarget == 'appservice' ? appServicePlan.outputs.id : ''
    runtimeName: 'python'
    runtimeVersion: '3.11'
    appCommandLine: 'python3 -m gunicorn main:app'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    virtualNetworkSubnetId: isolation.outputs.appSubnetId
    publicNetworkAccess: publicNetworkAccess
    allowedOrigins: [allowedOrigin]
    clientAppId: clientAppId
    serverAppId: serverAppId
    enableUnauthenticatedAccess: enableUnauthenticatedAccess
    disableAppServicesAuthentication: disableAppServicesAuthentication
    clientSecretSettingName: !empty(clientAppSecret) ? 'AZURE_CLIENT_APP_SECRET' : ''
    authenticationIssuerUri: authenticationIssuerUri
    use32BitWorkerProcess: appServiceSkuName == 'F1'
    alwaysOn: appServiceSkuName != 'F1'
    appSettings: appEnvVariables
  }
}

// Container Apps for the web application (Python Quart app with JS frontend)
module acaBackend 'core/host/container-app-upsert.bicep' = if (deploymentTarget == 'containerapps') {
  name: 'aca-web'
  scope: resourceGroup
  dependsOn: [
    containerApps
    acaIdentity
  ]
  params: {
    name: !empty(backendServiceName) ? backendServiceName : '${abbrs.webSitesContainerApps}backend-${resourceToken}'
    location: location
    identityName: (deploymentTarget == 'containerapps') ? acaIdentityName : ''
    exists: webAppExists
    workloadProfile: azureContainerAppsWorkloadProfile
    containerRegistryName: (deploymentTarget == 'containerapps') ? containerApps.outputs.registryName : ''
    containerAppsEnvironmentName: (deploymentTarget == 'containerapps') ? containerApps.outputs.environmentName : ''
    identityType: 'UserAssigned'
    tags: union(tags, { 'azd-service-name': 'backend' })
    targetPort: 8000
    containerCpuCoreCount: '1.0'
    containerMemory: '2Gi'
    allowedOrigins: [allowedOrigin]
    env: union(appEnvVariables, {
      // For using managed identity to access Azure resources. See https://github.com/microsoft/azure-container-apps/issues/442
      AZURE_CLIENT_ID: (deploymentTarget == 'containerapps') ? acaIdentity.outputs.clientId : ''
    })
  }
}

// Azure container apps resources (Only deployed if deploymentTarget is 'containerapps')
module containerApps 'core/host/container-apps.bicep' = if (deploymentTarget == 'containerapps') {
  name: 'container-apps'
  scope: resourceGroup
  params: {
    name: 'app'
    tags: tags
    location: location
    workloadProfile: azureContainerAppsWorkloadProfile
    containerAppsEnvironmentName: acaManagedEnvironmentName
    containerRegistryName: '${containerRegistryName}${resourceToken}'
    logAnalyticsWorkspaceResourceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

// User-assigned identity for pulling images from ACR
module acaIdentity 'core/security/aca-identity.bicep' = if (deploymentTarget == 'containerapps') {
  name: 'aca-identity'
  scope: resourceGroup
  params: {
    identityName: acaIdentityName
    location: location
  }
}

// === Cognitive Services ===

// Computer Vision Service
module computerVision 'br/public:avm/res/cognitive-services/account:0.5.4' = if (useGPT4V) {
  name: 'computerVision'
  scope: computerVisionResourceGroup
  params: {
    name: !empty(computerVisionServiceName)
      ? computerVisionServiceName
      : '${abbrs.cognitiveServicesComputerVision}${resourceToken}'
    kind: 'ComputerVision'
    networkAcls: {
      defaultAction: 'Allow'
    }
    customSubDomainName: !empty(computerVisionServiceName)
      ? computerVisionServiceName
      : '${abbrs.cognitiveServicesComputerVision}${resourceToken}'
    location: computerVisionResourceGroupLocation
    tags: tags
    sku: computerVisionSkuName
  }
}

// Document Intelligence Service (formerly Form Recognizer)
module documentIntelligence 'br/public:avm/res/cognitive-services/account:0.5.4' = {
  name: 'documentintelligence'
  scope: documentIntelligenceResourceGroup
  params: {
    name: !empty(documentIntelligenceServiceName)
      ? documentIntelligenceServiceName
      : '${abbrs.cognitiveServicesDocumentIntelligence}${resourceToken}'
    kind: 'FormRecognizer'
    customSubDomainName: !empty(documentIntelligenceServiceName)
      ? documentIntelligenceServiceName
      : '${abbrs.cognitiveServicesDocumentIntelligence}${resourceToken}'
    publicNetworkAccess: publicNetworkAccess
    networkAcls: {
      defaultAction: 'Allow'
    }
    location: documentIntelligenceResourceGroupLocation
    disableLocalAuth: true
    tags: tags
    sku: documentIntelligenceSkuName
  }
}

// Azure OpenAI setup
module openAi 'br/public:avm/res/cognitive-services/account:0.5.4' = if (isAzureOpenAiHost && deployAzureOpenAi) {
  name: 'openai'
  scope: openAiResourceGroup
  params: {
    name: !empty(openAiServiceName) ? openAiServiceName : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: openAiResourceGroupLocation
    tags: tags
    kind: 'OpenAI'
    customSubDomainName: !empty(openAiServiceName)
      ? openAiServiceName
      : '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    publicNetworkAccess: publicNetworkAccess
    networkAcls: {
      defaultAction: 'Allow'
      bypass: ipBypass
    }
    sku: openAiSkuName
    deployments: openAiDeployments
    disableLocalAuth: false
  }
}

// Speech Service
module speech 'br/public:avm/res/cognitive-services/account:0.5.4' = if (useSpeechOutputAzure) {
  name: 'speech-service'
  scope: speechResourceGroup
  params: {
    name: !empty(speechServiceName) ? speechServiceName : '${abbrs.cognitiveServicesSpeech}${resourceToken}'
    kind: 'SpeechServices'
    networkAcls: {
      defaultAction: 'Allow'
    }
    customSubDomainName: !empty(speechServiceName)
      ? speechServiceName
      : '${abbrs.cognitiveServicesSpeech}${resourceToken}'
    location: !empty(speechServiceLocation) ? speechServiceLocation : location
    tags: tags
    sku: speechServiceSkuName
  }
}

// === Monitoring ===

// Application Insights Dashboard for monitoring
module applicationInsightsDashboard 'backend-dashboard.bicep' = if (useApplicationInsights) {
  name: 'application-insights-dashboard'
  scope: resourceGroup
  params: {
    name: !empty(applicationInsightsDashboardName)
      ? applicationInsightsDashboardName
      : '${abbrs.portalDashboards}${resourceToken}'
    location: location
    applicationInsightsName: useApplicationInsights ? monitoring.outputs.applicationInsightsName : ''
  }
}

// Monitor application with Azure Monitor
module monitoring 'core/monitor/monitoring.bicep' = if (useApplicationInsights) {
  name: 'monitoring'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    applicationInsightsName: !empty(applicationInsightsName)
      ? applicationInsightsName
      : '${abbrs.insightsComponents}${resourceToken}'
    logAnalyticsName: !empty(logAnalyticsName)
      ? logAnalyticsName
      : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    publicNetworkAccess: publicNetworkAccess
  }
}

// Search Service Diagnostics
module searchDiagnostics 'core/search/search-diagnostics.bicep' = if (useApplicationInsights) {
  name: 'search-diagnostics'
  scope: searchServiceResourceGroup
  params: {
    searchServiceName: searchService.outputs.name
    workspaceId: useApplicationInsights ? monitoring.outputs.logAnalyticsWorkspaceId : ''
  }
}

// === Search ===

// Search Service
module searchService 'core/search/search-services.bicep' = {
  name: 'search-service'
  scope: searchServiceResourceGroup
  params: {
    name: !empty(searchServiceName) ? searchServiceName : 'gptkb-${resourceToken}'
    location: !empty(searchServiceLocation) ? searchServiceLocation : location
    tags: tags
    disableLocalAuth: true
    sku: {
      name: searchServiceSkuName
    }
    semanticSearch: actualSearchServiceSemanticRankerLevel
    publicNetworkAccess: publicNetworkAccess == 'Enabled'
      ? 'enabled'
      : (publicNetworkAccess == 'Disabled' ? 'disabled' : null)
    sharedPrivateLinkStorageAccounts: usePrivateEndpoint ? [storage.outputs.id] : []
  }
}

// === Storage ===

// Storage Account
module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: storageResourceGroup
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: storageResourceGroupLocation
    tags: tags
    publicNetworkAccess: publicNetworkAccess
    bypass: ipBypass
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    sku: {
      name: storageSkuName
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 2
    }
    containers: [
      {
        name: storageContainerName
        publicAccess: 'None'
      }
    ]
  }
}

// User Storage Account
module userStorage 'core/storage/storage-account.bicep' = if (useUserUpload) {
  name: 'user-storage'
  scope: storageResourceGroup
  params: {
    name: !empty(userStorageAccountName)
      ? userStorageAccountName
      : 'user${abbrs.storageStorageAccounts}${resourceToken}'
    location: storageResourceGroupLocation
    tags: tags
    publicNetworkAccess: publicNetworkAccess
    bypass: ipBypass
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    isHnsEnabled: true
    sku: {
      name: storageSkuName
    }
    containers: [
      {
        name: userStorageContainerName
        publicAccess: 'None'
      }
    ]
  }
}

module cognitiveServicesRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'cognitiveservices-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: principalType
  }
}

module computerVisionRoleBackend 'core/security/role.bicep' = if (useGPT4V) {
  scope: computerVisionResourceGroup
  name: 'computervision-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'ServicePrincipal'
  }
}

module documentIntelligenceRoleBackend 'core/security/role.bicep' = if (useUserUpload) {
  scope: documentIntelligenceResourceGroup
  name: 'documentintelligence-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'ServicePrincipal'
  }
}

module isolation 'network-isolation.bicep' = {
  name: 'networks'
  scope: resourceGroup
  params: {
    deploymentTarget: deploymentTarget
    location: location
    tags: tags
    vnetName: '${abbrs.virtualNetworks}${resourceToken}'
    // Need to check deploymentTarget due to https://github.com/Azure/bicep/issues/3990
    appServicePlanName: deploymentTarget == 'appservice' ? appServicePlan.outputs.name : ''
    usePrivateEndpoint: usePrivateEndpoint
  }
}

module openAiRoleBackend 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi) {
  scope: openAiResourceGroup
  name: 'openai-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

module openAiRoleSearchService 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi && useIntegratedVectorization) {
  scope: openAiResourceGroup
  name: 'openai-role-searchservice'
  params: {
    principalId: searchService.outputs.principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

module openAiRoleUser 'core/security/role.bicep' = if (isAzureOpenAiHost && deployAzureOpenAi) {
  scope: openAiResourceGroup
  name: 'openai-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: principalType
  }
}

module privateEndpoints 'private-endpoints.bicep' = if (usePrivateEndpoint && deploymentTarget == 'appservice') {
  name: 'privateEndpoints'
  scope: resourceGroup
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    privateEndpointConnections: privateEndpointConnections
    applicationInsightsId: useApplicationInsights ? monitoring.outputs.applicationInsightsId : ''
    logAnalyticsWorkspaceId: useApplicationInsights ? monitoring.outputs.logAnalyticsWorkspaceId : ''
    vnetName: isolation.outputs.vnetName
    vnetPeSubnetName: isolation.outputs.backendSubnetId
  }
}

module searchContribRoleBackend 'core/security/role.bicep' = if (useUserUpload) {
  scope: searchServiceResourceGroup
  name: 'search-contrib-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: 'ServicePrincipal'
  }
}

module searchContribRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: principalType
  }
}

module searchReaderRoleBackend 'core/security/role.bicep' = if (useAuthentication) {
  scope: searchServiceResourceGroup
  name: 'search-reader-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
    principalType: 'ServicePrincipal'
  }
}

module searchRoleBackend 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'ServicePrincipal'
  }
}

module searchRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: principalType
  }
}

module searchSvcContribRoleUser 'core/security/role.bicep' = {
  scope: searchServiceResourceGroup
  name: 'search-svccontrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
    principalType: principalType
  }
}

module speechRoleBackend 'core/security/role.bicep' = {
  scope: speechResourceGroup
  name: 'speech-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'f2dc8367-1007-4938-bd23-fe263f013447'
    principalType: 'ServicePrincipal'
  }
}

module speechRoleUser 'core/security/role.bicep' = {
  scope: speechResourceGroup
  name: 'speech-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'f2dc8367-1007-4938-bd23-fe263f013447'
    principalType: principalType
  }
}

module storageContribRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: principalType
  }
}

module storageOwnerRoleBackend 'core/security/role.bicep' = if (useUserUpload) {
  scope: storageResourceGroup
  name: 'storage-owner-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
    principalType: 'ServicePrincipal'
  }
}

module storageOwnerRoleUser 'core/security/role.bicep' = if (useUserUpload) {
  scope: storageResourceGroup
  name: 'storage-owner-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
    principalType: principalType
  }
}

module storageRoleBackend 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-backend'
  params: {
    principalId: (deploymentTarget == 'appservice')
      ? backend.outputs.identityPrincipalId
      : acaBackend.outputs.identityPrincipalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

module storageRoleSearchService 'core/security/role.bicep' = if (useIntegratedVectorization) {
  scope: storageResourceGroup
  name: 'storage-role-searchservice'
  params: {
    principalId: searchService.outputs.principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

module storageRoleUser 'core/security/role.bicep' = {
  scope: storageResourceGroup
  name: 'storage-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: principalType
  }
}

// === OUTPUTS ===

output AZURE_AUTH_TENANT_ID string = authTenantId
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = deploymentTarget == 'containerapps' ? containerApps.outputs.registryLoginServer : ''
output AZURE_DOCUMENTINTELLIGENCE_RESOURCE_GROUP string = documentIntelligenceResourceGroup.name
output AZURE_DOCUMENTINTELLIGENCE_SERVICE string = documentIntelligence.outputs.name
output AZURE_LOCATION string = location
output AZURE_OPENAI_API_VERSION string = isAzureOpenAiHost ? azureOpenAiApiVersion : ''
output AZURE_OPENAI_CHATGPT_DEPLOYMENT string = isAzureOpenAiHost ? chatGpt.deploymentName : ''
output AZURE_OPENAI_CHATGPT_MODEL string = chatGpt.modelName
output AZURE_OPENAI_EMB_DEPLOYMENT string = isAzureOpenAiHost ? embedding.deploymentName : ''
output AZURE_OPENAI_EMB_MODEL_NAME string = embedding.modelName
output AZURE_OPENAI_GPT4V_DEPLOYMENT string = isAzureOpenAiHost ? gpt4vDeploymentName : ''
output AZURE_OPENAI_GPT4V_MODEL string = gpt4vModelName
output AZURE_OPENAI_RESOURCE_GROUP string = isAzureOpenAiHost ? openAiResourceGroup.name : ''
output AZURE_OPENAI_SERVICE string = isAzureOpenAiHost && deployAzureOpenAi ? openAi.outputs.name : ''
output AZURE_RESOURCE_GROUP string = resourceGroup.name
output AZURE_SEARCH_INDEX string = searchIndexName
output AZURE_SEARCH_SEMANTIC_RANKER string = actualSearchServiceSemanticRankerLevel
output AZURE_SEARCH_SERVICE string = searchService.outputs.name
output AZURE_SEARCH_SERVICE_ASSIGNED_USERID string = searchService.outputs.principalId
output AZURE_SEARCH_SERVICE_RESOURCE_GROUP string = searchServiceResourceGroup.name
output AZURE_SPEECH_SERVICE_ID string = useSpeechOutputAzure ? speech.outputs.resourceId : ''
output AZURE_SPEECH_SERVICE_LOCATION string = useSpeechOutputAzure ? speech.outputs.location : ''
output AZURE_STORAGE_ACCOUNT string = storage.outputs.name
output AZURE_STORAGE_CONTAINER string = storageContainerName
output AZURE_STORAGE_RESOURCE_GROUP string = storageResourceGroup.name
output AZURE_TENANT_ID string = tenantId
output AZURE_USE_AUTHENTICATION bool = useAuthentication
output AZURE_USERSTORAGE_ACCOUNT string = useUserUpload ? userStorage.outputs.name : ''
output AZURE_USERSTORAGE_CONTAINER string = userStorageContainerName
output AZURE_USERSTORAGE_RESOURCE_GROUP string = storageResourceGroup.name
output AZURE_VISION_ENDPOINT string = useGPT4V ? computerVision.outputs.endpoint : ''
output BACKEND_URI string = deploymentTarget == 'appservice' ? backend.outputs.uri : acaBackend.outputs.uri
output OPENAI_HOST string = openAiHost
output USE_FEATURE_INT_VECTORIZATION bool = useIntegratedVectorization
