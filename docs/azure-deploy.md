# Azure Deployment Runbook

This runbook deploys `ocuwell-gateway` to Azure App Service in
`rg-ocuwell-gateway`.

Do not paste secrets into chat, commits, logs, or screenshots. Put
LicenseSpring secrets into Azure Key Vault through the Azure portal, then use
Key Vault references in App Service settings.

## Current Azure Targets

- Resource group: `rg-ocuwell-gateway`
- Region: `uksouth`
- App Service plan: `asp-ocuwell-gateway-uksouth`
- Web app: `ocuwell-gateway`
- Web app URL: `https://ocuwell-gateway.azurewebsites.net`
- Key Vault: `kv-ocuwell-gateway`
- Azure SQL server: `ocuwell-gateway.database.windows.net`
- Azure SQL database: `ocuwell-gateway`

## 1. Build and Test Locally

```powershell
cd C:\Users\chaya\GitHub\ocuwell-gateway

cd apps\ui
npm ci
npm run build
cd ..\..

.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pytest
```

Commit the release state before packaging:

```powershell
git status --short
git add <changed-files>
git commit -m "Prepare Azure gateway deployment"
```

## 2. Create or Confirm Azure Resources

```powershell
$RG = "rg-ocuwell-gateway"
$LOCATION = "uksouth"
$PLAN = "asp-ocuwell-gateway-uksouth"
$APP = "ocuwell-gateway"
$KV = "kv-ocuwell-gateway"
$SQL_SERVER = "ocuwell-gateway"
$SQL_DB = "ocuwell-gateway"

az group show --name $RG

az appservice plan create `
  --resource-group $RG `
  --name $PLAN `
  --location $LOCATION `
  --is-linux `
  --sku B1

az webapp create `
  --resource-group $RG `
  --plan $PLAN `
  --name $APP `
  --runtime "PYTHON:3.11"

az keyvault create `
  --resource-group $RG `
  --name $KV `
  --location $LOCATION
```

## 3. Configure App Service

```powershell
az webapp config set `
  --resource-group $RG `
  --name $APP `
  --always-on true `
  --http20-enabled true `
  --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 apps.main:app"

az webapp update `
  --resource-group $RG `
  --name $APP `
  --https-only true

az webapp config appsettings set `
  --resource-group $RG `
  --name $APP `
  --settings `
    SCM_DO_BUILD_DURING_DEPLOYMENT=true `
    ENABLE_ORYX_BUILD=true `
    DB_BACKEND=azure_sql `
    AZURE_SQL_AUTH_MODE=entra `
    AZURE_SQL_SERVER=ocuwell-gateway.database.windows.net `
    AZURE_SQL_PORT=1433 `
    AZURE_SQL_DATABASE=ocuwell-gateway `
    AZURE_SQL_DRIVER="ODBC Driver 18 for SQL Server" `
    AZURE_SQL_ENCRYPT=yes `
    AZURE_SQL_TRUST_SERVER_CERTIFICATE=no `
    AZURE_SQL_CONNECTION_TIMEOUT=30 `
    AZURE_SQL_EXCLUDE_INTERACTIVE_BROWSER_CREDENTIAL=true `
    LICENSESPRING_API_PROTOCOL=https `
    LICENSESPRING_API_DOMAIN=api.licensespring.com `
    LICENSESPRING_API_VERSION=v4
```

## 4. Store LicenseSpring Secrets in Key Vault

In Azure portal, open `kv-ocuwell-gateway` and create these secrets:

- `licensespring-api-key`
- `licensespring-shared-key`
- `licensespring-product-code`

Then grant the web app managed identity permission to read secrets:

```powershell
$principalId = az webapp identity show `
  --resource-group $RG `
  --name $APP `
  --query principalId `
  --output tsv

az keyvault set-policy `
  --name $KV `
  --resource-group $RG `
  --object-id $principalId `
  --secret-permissions get list
```

Set App Service settings to Key Vault references:

```powershell
$apiKeyUri = az keyvault secret show --vault-name $KV --name licensespring-api-key --query id --output tsv
$sharedKeyUri = az keyvault secret show --vault-name $KV --name licensespring-shared-key --query id --output tsv
$productCodeUri = az keyvault secret show --vault-name $KV --name licensespring-product-code --query id --output tsv

az webapp config appsettings set `
  --resource-group $RG `
  --name $APP `
  --settings `
    LICENSESPRING_API_KEY="@Microsoft.KeyVault(SecretUri=$apiKeyUri)" `
    LICENSESPRING_SHARED_KEY="@Microsoft.KeyVault(SecretUri=$sharedKeyUri)" `
    LICENSESPRING_PRODUCT_CODE="@Microsoft.KeyVault(SecretUri=$productCodeUri)"
```

## 5. Grant Azure SQL Access

Sign in to Azure SQL as the Entra admin, then run this against the
`ocuwell-gateway` database:

```sql
CREATE USER [ocuwell-gateway] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [ocuwell-gateway];
ALTER ROLE db_datawriter ADD MEMBER [ocuwell-gateway];
```

Run Alembic migrations from a trusted admin workstation:

```powershell
$env:DB_BACKEND = "azure_sql"
$env:AZURE_SQL_AUTH_MODE = "entra"
$env:AZURE_SQL_CREDENTIAL = "azure_cli"
$env:AZURE_SQL_SERVER = "ocuwell-gateway.database.windows.net"
$env:AZURE_SQL_PORT = "1433"
$env:AZURE_SQL_DATABASE = "ocuwell-gateway"
$env:AZURE_SQL_DRIVER = "ODBC Driver 18 for SQL Server"
$env:AZURE_SQL_ENCRYPT = "yes"
$env:AZURE_SQL_TRUST_SERVER_CERTIFICATE = "no"
$env:AZURE_SQL_EXCLUDE_INTERACTIVE_BROWSER_CREDENTIAL = "true"

.\.venv\Scripts\alembic upgrade head
```

## 6. Package and Deploy

```powershell
New-Item -ItemType Directory -Force .tmp | Out-Null
git archive --format zip --output .tmp\ocuwell-gateway.zip HEAD

az webapp deploy `
  --resource-group $RG `
  --name $APP `
  --src-path .tmp\ocuwell-gateway.zip `
  --type zip

az webapp restart `
  --resource-group $RG `
  --name $APP
```

## 7. Verify

```powershell
Invoke-WebRequest https://ocuwell-gateway.azurewebsites.net/health -UseBasicParsing
Invoke-WebRequest https://ocuwell-gateway.azurewebsites.net/ui/ -UseBasicParsing

az webapp log tail `
  --resource-group $RG `
  --name $APP
```

Manual release smoke tests:

- `/health` returns `200`.
- `/ui/` loads.
- `/ui/assets/*.js` and `/ui/assets/*.css` return `200`.
- Online activation through the desktop app works.
- Online deactivation through the desktop app works.
- Offline activation request file upload returns a `.lic` file.
- Offline deactivation request file upload returns success.
- QR transfer is tested separately because camera glare can affect scanning.

