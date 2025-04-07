# Deploying CountyDataSync to Azure

This guide provides instructions for deploying CountyDataSync to Microsoft Azure Cloud services.

## Prerequisites

- Azure CLI installed and configured (`az login` completed)
- Azure subscription with appropriate permissions
- CountyDataSync package created with `python package_application.py --azure`

## Deployment Options

CountyDataSync can be deployed to Azure in several ways:

1. **Azure App Service**: For web application deployment
2. **Azure Virtual Machine**: For full control over the environment
3. **Azure Container Instances**: For containerized deployment

## Azure App Service Deployment

### Step 1: Create Azure Resources

You can use the Azure CLI or the included ARM template:

```bash
# Create a resource group if needed
az group create --name CountyDataSyncRG --location eastus

# Deploy using the ARM template
az deployment group create \
  --resource-group CountyDataSyncRG \
  --template-file azure-config/template.json \
  --parameters appServiceName=countydatasync
```

### Step 2: Deploy the Application

```bash
# Deploy the app using the deployment script
cd CountyDataSync-<version>/azure-config
./deploy.sh CountyDataSyncRG countydatasync
```

### Step 3: Configure Application Settings

```bash
# Set environment variables
az webapp config appsettings set \
  --resource-group CountyDataSyncRG \
  --name countydatasync \
  --settings \
  "DATABASE_URL=<your-database-url>" \
  "MSSQL_SERVER=<your-sql-server>" \
  "MSSQL_DATABASE=<your-database-name>" \
  "MSSQL_USERNAME=<your-username>" \
  "MSSQL_PASSWORD=<your-password>"
```

## Azure Virtual Machine Deployment

### Step 1: Create a VM

```bash
# Create a Windows VM (for Windows version)
az vm create \
  --resource-group CountyDataSyncRG \
  --name countydatasync-vm \
  --image Win2019Datacenter \
  --admin-username azureuser \
  --admin-password <SecurePassword>
```

### Step 2: Upload and Install

1. Connect to the VM using RDP
2. Upload the CountyDataSync package
3. Extract and install the application
4. Configure as a service (optional)

## Azure Container Deployment

For containerized deployment, you need to create a Docker image first:

### Step 1: Create a Docker image

Create a Dockerfile in your project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY CountyDataSync-<version>/ .

ENV USE_TEST_DATA=false

EXPOSE 8080

CMD ["./CountyDataSync"]
```

### Step 2: Build and push to Azure Container Registry

```bash
# Create ACR
az acr create --resource-group CountyDataSyncRG --name countydatasyncacr --sku Basic

# Build and push
az acr build --registry countydatasyncacr --image countydatasync:latest .
```

### Step 3: Deploy to Azure Container Instances

```bash
# Deploy container
az container create \
  --resource-group CountyDataSyncRG \
  --name countydatasync-container \
  --image countydatasyncacr.azurecr.io/countydatasync:latest \
  --registry-login-server countydatasyncacr.azurecr.io \
  --registry-username $(az acr credential show -n countydatasyncacr --query username -o tsv) \
  --registry-password $(az acr credential show -n countydatasyncacr --query passwords[0].value -o tsv) \
  --dns-name-label countydatasync \
  --ports 8080
```

## Azure Best Practices

1. **Security**:
   - Use Azure Key Vault for sensitive configuration
   - Enable HTTPS for all communications
   - Use managed identities for authentication

2. **Scaling**:
   - Configure auto-scaling based on usage patterns
   - Use Azure Application Insights for monitoring

3. **Data Storage**:
   - Use Azure SQL Database for relational data
   - Use Azure Blob Storage for file storage
   - Consider Azure CosmosDB for NoSQL data

4. **Cost Management**:
   - Choose appropriate pricing tiers
   - Use Azure Cost Management to monitor expenses
   - Consider reserved instances for long-term deployments

## Troubleshooting

1. **Deployment Issues**:
   - Check application logs: `az webapp log tail --name countydatasync --resource-group CountyDataSyncRG`
   - Verify application settings are correct

2. **Application Errors**:
   - Enable diagnostic logs in Azure Portal
   - Set up Azure Application Insights

3. **Performance Issues**:
   - Check CPU and memory metrics in Azure Portal
   - Consider scaling up or out

## Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Virtual Machines Documentation](https://docs.microsoft.com/en-us/azure/virtual-machines/)
- [Azure Container Instances Documentation](https://docs.microsoft.com/en-us/azure/container-instances/)
