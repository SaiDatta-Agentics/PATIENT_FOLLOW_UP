# Azure deployment — CareFlow AI v3

The project is packaged as one production container: React is compiled in a Node build stage and copied into the FastAPI image. Azure Container Apps therefore exposes one app/URL for both the UI, REST API and WebSocket live-update endpoint.

## Resources used by `deploy-azure.ps1`

- Resource Group
- Azure Container Registry
- Azure Container Apps Environment + Container App
- Azure Database for PostgreSQL Flexible Server
- Azure OpenAI resource + model deployment
- Azure Communication Services
- Azure Storage account + `patient-files` blob container

The app also accepts secrets through Container Apps. For stricter production secret governance, replace direct secrets with Key Vault references/managed identity.

## Before running

1. Install Azure CLI and Docker if you also want local Docker testing.
2. `az login`
3. `az account list --output table`
4. `az account set --subscription "YOUR-SUBSCRIPTION-ID"`
5. From the project root, verify the Azure OpenAI model and version available to your subscription/region. The script parameters are intentionally overrideable.

## Deploy

```powershell
.\azure\deploy-azure.ps1
```

Optional example with another available model/version:

```powershell
.\azure\deploy-azure.ps1 `
  -Location "eastus2" `
  -ModelName "YOUR_AVAILABLE_MODEL" `
  -ModelVersion "YOUR_AVAILABLE_MODEL_VERSION" `
  -DeploymentName "followup-gpt"
```

The script prompts for:

- PostgreSQL admin password
- JWT secret
- Doctor/staff clinic registration access code

After completion it prints the public Container App URL and health endpoint.

## SMS / voice

Azure Communication Services is created, but acquiring a usable phone number depends on subscription eligibility, region and regulatory requirements. Until `AZURE_SMS_FROM_NUMBER` / caller ID values are configured, the app intentionally uses simulated outbound communication while still logging events to the same conversation workflow.

## Production note

For real patient health information, use your organization's required compliance controls: verified patient identity, private networking, managed identity, Key Vault, audit/retention policy, backups, monitoring, consent/communications policy and clinical governance.
