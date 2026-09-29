param(
  [string]$Location = "eastus2",
  [string]$ResourceGroup = "saidatta-followup-rg",
  [string]$ModelName = "gpt-4o",
  [string]$ModelVersion = "2024-11-20",
  [string]$DeploymentName = "followup-gpt"
)
$ErrorActionPreference = "Stop"
$Suffix = Get-Random -Minimum 10000 -Maximum 99999
$Acr = "saidattafollowupacr$Suffix"
$Storage = "saidattafollowup$Suffix"
$Pg = "saidatta-followup-pg-$Suffix"
$Ai = "saidatta-followup-ai-$Suffix"
$Acs = "saidatta-followup-acs-$Suffix"
$Env = "saidatta-followup-env"
$App = "saidatta-followup-agent"
$Db = "followupdb"
$DbUser = "followupadmin"
$DbPassword = Read-Host "Enter a strong PostgreSQL admin password"
$JwtSecret = Read-Host "Enter a long random JWT secret"
$ClinicAccessCode = Read-Host "Enter a clinic access code for doctor/staff registration"

az extension add --name containerapp --upgrade
az extension add --name communication --upgrade
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.ContainerRegistry --wait
az provider register --namespace Microsoft.CognitiveServices --wait
az provider register --namespace Microsoft.Communication --wait
az provider register --namespace Microsoft.Storage --wait
az provider register --namespace Microsoft.DBforPostgreSQL --wait

az group create -n $ResourceGroup -l $Location | Out-Null
az acr create -g $ResourceGroup -n $Acr --sku Basic --admin-enabled true | Out-Null
az storage account create -g $ResourceGroup -n $Storage -l $Location --sku Standard_LRS --kind StorageV2 --https-only true | Out-Null
$StorageConnection = az storage account show-connection-string -g $ResourceGroup -n $Storage --query connectionString -o tsv
az storage container create --name patient-files --connection-string $StorageConnection | Out-Null

az postgres flexible-server create -g $ResourceGroup -n $Pg -l $Location --admin-user $DbUser --admin-password $DbPassword --sku-name Standard_B1ms --tier Burstable --storage-size 32 --version 16 --public-access 0.0.0.0 | Out-Null
az postgres flexible-server db create -g $ResourceGroup --server-name $Pg --database-name $Db | Out-Null
$DatabaseUrl = "postgresql+asyncpg://${DbUser}:${DbPassword}@${Pg}.postgres.database.azure.com:5432/${Db}?ssl=require"

az cognitiveservices account create -g $ResourceGroup -n $Ai -l $Location --kind OpenAI --sku S0 --custom-domain $Ai | Out-Null
az cognitiveservices account deployment create -g $ResourceGroup -n $Ai --deployment-name $DeploymentName --model-name $ModelName --model-version $ModelVersion --model-format OpenAI --sku-name GlobalStandard --sku-capacity 1 | Out-Null
$AiEndpoint = az cognitiveservices account show -g $ResourceGroup -n $Ai --query properties.endpoint -o tsv
$AiKey = az cognitiveservices account keys list -g $ResourceGroup -n $Ai --query key1 -o tsv

az communication create -g $ResourceGroup -n $Acs --location Global --data-location UnitedStates | Out-Null
$AcsConnection = az communication list-key -g $ResourceGroup -n $Acs --query primaryConnectionString -o tsv

az containerapp env create -g $ResourceGroup -n $Env -l $Location | Out-Null
az acr build -r $Acr -t patient-followup:v3 .
$AcrServer = az acr show -g $ResourceGroup -n $Acr --query loginServer -o tsv
$AcrUser = az acr credential show -n $Acr --query username -o tsv
$AcrPassword = az acr credential show -n $Acr --query 'passwords[0].value' -o tsv

az containerapp create `
  -g $ResourceGroup -n $App --environment $Env `
  --image "$AcrServer/patient-followup:v3" `
  --registry-server $AcrServer --registry-username $AcrUser --registry-password $AcrPassword `
  --ingress external --target-port 8000 --min-replicas 1 --max-replicas 1 --cpu 0.5 --memory 1Gi `
  --secrets "db-url=$DatabaseUrl" "jwt-secret=$JwtSecret" "openai-key=$AiKey" "storage-connection=$StorageConnection" "acs-connection=$AcsConnection" "clinic-code=$ClinicAccessCode" `
  --env-vars "DEMO_MODE=true" "AUTO_FOLLOWUP_ENABLED=true" "FOLLOWUP_POLL_SECONDS=15" "DATABASE_URL=secretref:db-url" "SECRET_KEY=secretref:jwt-secret" "AZURE_OPENAI_ENDPOINT=$AiEndpoint" "AZURE_OPENAI_KEY=secretref:openai-key" "AZURE_OPENAI_DEPLOYMENT=$DeploymentName" "AZURE_STORAGE_CONNECTION_STRING=secretref:storage-connection" "AZURE_COMMUNICATION_CONNECTION_STRING=secretref:acs-connection" "CLINIC_ACCESS_CODE=secretref:clinic-code"

$Fqdn = az containerapp show -g $ResourceGroup -n $App --query properties.configuration.ingress.fqdn -o tsv
Write-Host "Deployment complete: https://$Fqdn"
Write-Host "Health: https://$Fqdn/api/health"
Write-Host "IMPORTANT: acquire an Azure Communication Services phone number and set AZURE_SMS_FROM_NUMBER / AZURE_CALLER_ID before real SMS or voice sends. Until then the application should be kept in simulated communication mode."
