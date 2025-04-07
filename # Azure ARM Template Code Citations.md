# Azure ARM Template Code Citations

This document contains code citations for Azure ARM templates used in the CountyDataSync project. These snippets follow Azure best practices and are sourced from official Microsoft documentation.

## ARM Template Schema

The ARM template schema defines the structure for Azure Resource Manager templates. All ARM templates should use this schema reference:

### License: MIT
Source: [Microsoft Azure Docs - App Insights Migration](https://github.com/MicrosoftDocs/azure-docs/blob/80a221eea5c7efd322b4402f7db8cf113575d01f/articles/azure-monitor/app/migrate-from-instrumentation-keys-to-connection-strings.md)

```json
"$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
"contentVersion": "1.0.0.0",
```

## ARM Template Best Practices

### Parameter Definitions
Parameters should include descriptive metadata and appropriate default values:

```json
"parameters": {
    "appServiceName": {
        "type": "string",
        "metadata": {
            "description": "Name of the App Service"
        }
    },
    "location": {
        "type": "string",
        "defaultValue": "[resourceGroup().location]",
        "metadata": {
            "description": "Location for resources"
        }
    },
    "sku": {
        "type": "string",
        "defaultValue": "S1",
        "allowedValues": ["F1", "D1", "B1", "B2", "B3", "S1", "S2", "S3", "P1v2", "P2v2", "P3v2"],
        "metadata": {
            "description": "App Service plan SKU"
        }
    }
}
```

### Resource Definitions
Resources should include dependencies and proper reference patterns:

```json
{
    "type": "Microsoft.Web/serverfarms",
    "apiVersion": "2021-02-01",
    "name": "[variables('appServicePlanName')]",
    "location": "[parameters('location')]",
    "sku": {
        "name": "[parameters('sku')]"
    },
    "kind": "app",
    "properties": {
        "reserved": false
    }
},
{
    "type": "Microsoft.Web/sites",
    "apiVersion": "2021-02-01",
    "name": "[parameters('appServiceName')]",
    "location": "[parameters('location')]",
    "dependsOn": [
        "[resourceId('Microsoft.Web/serverfarms', variables('appServicePlanName'))]"
    ],
    "properties": {
        "serverFarmId": "[resourceId('Microsoft.Web/serverfarms', variables('appServicePlanName'))]",
        "httpsOnly": true,
        "siteConfig": {
            "alwaysOn": true,
            "minTlsVersion": "1.2"
        }
    }
}
```

## Azure Best Practices Implementation

These code snippets implement the following Azure best practices:

1. **Schema Versioning**: Using the latest schema version
2. **Parameterization**: Making templates flexible with parameters
3. **Resource Dependencies**: Defining correct resource dependencies
4. **Security Configurations**: 
   - HTTPS-only setting
   - Minimum TLS version 1.2
5. **Consistent Naming**: Using variables for consistent resource naming

## References

For more information on Azure ARM template best practices, see:
- [ARM template best practices](https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/best-practices)
- [Azure subscription and service limits](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits)

