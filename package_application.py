#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Package CountyDataSync for distribution.

This script creates a complete distribution package with the standalone executable,
configuration files, and documentation. It also supports Azure deployment preparation.

Usage:
    python package_application.py [--version VERSION] [--check-only] [--test] [--azure] [--installer]

Arguments:
    --version VERSION: Version string to use for the package (default: current date)
    --check-only: Only check prerequisites without building package
    --test: Run tests on the packaged executable after building
    --azure: Prepare package for Azure deployment
    --installer: Create platform-specific installer
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
import zipfile
import importlib
import json

# Constants
REQUIRED_PACKAGES = [
    'pandas', 'numpy', 'geopandas', 'pyodbc', 'sqlalchemy', 
    'shapely', 'psutil', 'python-dotenv', 'flask', 'pyinstaller'
]

# Additional Azure packages that may be needed
AZURE_PACKAGES = [
    'azure-storage-blob', 'azure-identity', 'azure-mgmt-resource',
    'azure-mgmt-web', 'azure-mgmt-monitor', 'azure-mgmt-applicationinsights'
]

# Python executable detection
def get_python_executable():
    """
    Determine the correct Python executable to use in subprocess calls.
    This helps avoid the 'spawn python ENOENT' error when Python isn't in PATH.
    """
    # Return the executable used to run this script
    if hasattr(sys, 'executable') and sys.executable:
        return sys.executable
    
    # Try common executable names with more robust error handling
    for cmd in ['python3', 'python', 'py', 'python3.9', 'python3.10', 'python3.11']:
        try:
            # Check if the command exists and returns a version
            # Add a shell=True option on Windows to better handle PATH issues
            use_shell = platform.system() == 'Windows'
            result = subprocess.run([cmd, '--version'], 
                                   capture_output=True, text=True, 
                                   timeout=2, shell=use_shell)
            if result.returncode == 0:
                return cmd
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            continue
    
    # Try to find Python in common installation locations
    common_locations = []
    
    if platform.system() == 'Windows':
        # Windows common Python locations
        drive = os.environ.get('SystemDrive', 'C:')
        for version in ['39', '310', '311', '312', '38', '37']:
            common_locations.extend([
                f"{drive}\\Python{version}\\python.exe",
                f"{drive}\\Program Files\\Python{version}\\python.exe",
                f"{drive}\\Program Files (x86)\\Python{version}\\python.exe",
                f"{os.environ.get('LOCALAPPDATA', '')}\\Programs\\Python\\Python{version}\\python.exe",
            ])
    else:
        # Unix-like common Python locations
        for version in ['3.9', '3.10', '3.11', '3.12', '3.8', '3.7']:
            common_locations.extend([
                f"/usr/bin/python{version}",
                f"/usr/local/bin/python{version}",
                f"/opt/python{version}/bin/python",
                f"{os.environ.get('HOME', '')}/anaconda3/bin/python",
                f"{os.environ.get('HOME', '')}/miniconda3/bin/python",
            ])
    
    # Try each location
    for location in common_locations:
        if os.path.exists(location) and os.access(location, os.X_OK):
            try:
                result = subprocess.run([location, '--version'], 
                                      capture_output=True, text=True, 
                                      timeout=2)
                if result.returncode == 0:
                    return location
            except (subprocess.SubprocessError, OSError):
                continue
    
    # If we get here, we couldn't find a Python executable
    return None

# Global variable for Python executable
PYTHON_EXECUTABLE = get_python_executable()

def check_python_path():
    """Check if Python is correctly set up in the PATH."""
    if not PYTHON_EXECUTABLE:
        print("❌ Python executable not found in PATH")
        print("\nTroubleshooting steps:")
        print("1. Ensure Python 3 is installed")
        print("2. Make sure Python is added to your PATH environment variable")
        print("   - Windows: Check 'Add Python to PATH' during installation")
        print("   - macOS/Linux: Add 'export PATH=$PATH:/path/to/python/bin' to your shell profile")
        print("3. Try specifying the full path to Python when running this script")
        print("   Example: /usr/bin/python3 package_application.py")
        if platform.system() == 'Windows':
            print("\nOn Windows, you can also try running:")
            print("   py package_application.py")
        return False
    else:
        print(f"✓ Python executable found: {PYTHON_EXECUTABLE}")
        return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Package CountyDataSync for distribution')
    
    # Version argument with default to current date
    default_version = datetime.now().strftime('%Y%m%d')
    parser.add_argument('--version', type=str, default=default_version,
                       help='Version string for the package (default: current date)')
    
    # Add new arguments
    parser.add_argument('--check-only', action='store_true',
                       help='Only check prerequisites without building package')
    parser.add_argument('--test', action='store_true',
                       help='Run tests on the packaged executable after building')
    parser.add_argument('--azure', action='store_true',
                       help='Prepare package for Azure deployment')
    parser.add_argument('--installer', action='store_true',
                       help='Create platform-specific installer')
    
    return parser.parse_args()

def check_prerequisites():
    """Check if all required software and libraries are installed."""
    print("\nChecking prerequisites...")
    
    # First check Python PATH setup
    if not check_python_path():
        return False
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("❌ Python 3.7+ is required. Current version:", sys.version)
        return False
    else:
        print(f"✓ Python version: {sys.version}")
    
    # Check required packages
    missing_packages = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print("\nMissing packages:", ", ".join(missing_packages))
        print("Please install them using: pip install", " ".join(missing_packages))
        return False
    
    # Check if build_executable.py exists   
    if not os.path.exists('build_executable.py'):
        print("❌ build_executable.py not found.")
        return False
    else:
        print("✓ build_executable.py found")
    
    print("✓ All prerequisites met!")
    return True

def check_spec_file():
    """Check if PyInstaller spec file exists or needs to be generated."""
    print("\nChecking PyInstaller spec file...")
    
    spec_file = 'countydatasync.spec'
    if os.path.exists(spec_file):
        print(f"✓ Spec file {spec_file} exists")
        # Check if spec file needs updating (e.g., by comparing timestamps)
        return True
    else:
        print(f"❌ Spec file {spec_file} not found")
        # Try to generate spec file
        try:
            if os.path.exists('generate_spec.py'):
                print("Attempting to generate spec file using generate_spec.py...")
                result = subprocess.run([PYTHON_EXECUTABLE, 'generate_spec.py'],
                                       check=True, capture_output=True, text=True)
                if os.path.exists(spec_file):
                    print(f"✓ Successfully generated {spec_file}")
                    return True
                else:
                    print(f"❌ Failed to generate {spec_file}")
            else:
                print("❌ generate_spec.py not found")
        except Exception as e:
            print(f"❌ Error generating spec file: {str(e)}")
    
    print("\nYou may need to manually create a spec file using:")
    print(f"  {PYTHON_EXECUTABLE} -m PyInstaller --onefile --name countydatasync main.py")
    return False

def build_executable():
    """Build the executable using build_executable.py."""
    print("\nBuilding executable...")
    
    try:
        # Check if build_executable.py exists
        if not os.path.exists('build_executable.py'):
            print("Error: build_executable.py not found.")
            return False
        
        # Run the build script
        result = subprocess.run([PYTHON_EXECUTABLE, 'build_executable.py'],
                               check=True, capture_output=True, text=True)
        
        # Check for successful build
        exe_path = os.path.join('dist', 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else ''))
        if os.path.exists(exe_path):
            print("✓ Executable built successfully!")
            return True
        else:
            print("❌ Failed to build executable.")
            print(result.stdout)
            print(result.stderr)
            return False
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}:")
        print(e.stdout)
        print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ Error: Could not execute Python. Make sure Python is installed and in your PATH.")
        print(f"   Current Python path: {PYTHON_EXECUTABLE}")
        return False
    except Exception as e:
        print(f"❌ Build failed with error: {str(e)}")
        return False

def copy_documentation(dist_dir):
    """Copy documentation files to distribution directory."""
    print("\nCopying documentation...")
    
    # List of documentation files to copy
    doc_files = [
        'README.md',
        'INSTALLATION.md',
        'PACKAGING.txt',
        'docs/UserGuide.md',
        'docs/AdminGuide.md',
        'LICENSE',
        'CHANGELOG.md'
    ]
    
    # Copy each file if it exists
    docs_copied = 0
    for file in doc_files:
        if os.path.exists(file):
            # Create subdirectories if needed
            dest_path = os.path.join(dist_dir, file)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file, dest_path)
            print(f"✓ Copied {file}")
            docs_copied += 1
        else:
            print(f"Note: {file} not found, skipping.")
    
    if docs_copied == 0:
        # Create a basic README if no docs exist
        readme_path = os.path.join(dist_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write("# CountyDataSync\n\n")
            f.write("CountyDataSync is a tool for synchronizing county geo and statistical data.\n\n")
            f.write("## Basic Usage\n\n")
            f.write("1. Configure the application by editing the .env file\n")
            f.write("2. Run CountyDataSync executable\n")
            f.write("3. Check the 'output' directory for results\n")
        print("✓ Created basic README.md")

def copy_config_files(dist_dir):
    """Copy configuration files to distribution directory."""
    print("\nCopying configuration files...")
    
    # Copy .env.example if it exists
    if os.path.exists('.env.example'):
        shutil.copy2('.env.example', os.path.join(dist_dir, '.env.example'))
        print("✓ Copied .env.example")
    else:
        # Create a basic .env.example file
        with open(os.path.join(dist_dir, '.env.example'), 'w') as f:
            f.write("# CountyDataSync Environment Configuration\n\n")
            f.write("# Database connection (PostgreSQL or SQLite)\n")
            f.write("DATABASE_URL=sqlite:///instance/countydatasync.db\n\n")
            f.write("# SQL Server connection (for data extraction)\n")
            f.write("MSSQL_SERVER=your_server_address\n")
            f.write("MSSQL_DATABASE=your_database_name\n")
            f.write("MSSQL_USERNAME=your_username\n")
            f.write("MSSQL_PASSWORD=your_password\n\n")
            f.write("# Set to 'true' to use test data instead of SQL Server\n")
            f.write("USE_TEST_DATA=false\n")
        print("✓ Created .env.example")
    
    # Copy config.py if it exists
    if os.path.exists('config.py'):
        shutil.copy2('config.py', dist_dir)
        print("✓ Copied config.py")
    
    # Create Azure deployment configuration if needed
    if args.azure:
        create_azure_config(dist_dir)

def create_azure_config(dist_dir):
    """Create Azure deployment configuration files."""
    print("\nCreating Azure deployment configuration...")
    
    # Import Azure-specific modules if available
    try:
        import importlib
        # Check for Azure packages
        azure_pkgs_missing = []
        for pkg in AZURE_PACKAGES:
            try:
                importlib.import_module(pkg)
            except ImportError:
                azure_pkgs_missing.append(pkg)
        
        if azure_pkgs_missing:
            print(f"\n⚠️ Some Azure packages are missing: {', '.join(azure_pkgs_missing)}")
            print("Consider installing them with: pip install " + " ".join(azure_pkgs_missing))
    except Exception:
        pass
    
    # Create azure-config folder
    azure_dir = os.path.join(dist_dir, 'azure-config')
    os.makedirs(azure_dir, exist_ok=True)
    
    # Create Azure App Service configuration
    web_config_path = os.path.join(azure_dir, 'web.config')
    with open(web_config_path, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<configuration>\n')
        f.write('  <system.webServer>\n')
        f.write('    <handlers>\n')
        f.write('      <add name="httpPlatformHandler" path="*" verb="*" modules="httpPlatformHandler" resourceType="Unspecified" />\n')
        f.write('    </handlers>\n')
        f.write('    <httpPlatform processPath="%HOME%\\site\\wwwroot\\CountyDataSync.exe" \n')
        f.write('                  arguments="" \n')
        f.write('                  stdoutLogEnabled="true" \n')
        f.write('                  stdoutLogFile="%HOME%\\LogFiles\\stdout" \n')
        f.write('                  startupTimeLimit="60" \n')
        f.write('                  requestTimeout="00:05:00" />\n')
        f.write('  </system.webServer>\n')
        f.write('</configuration>\n')
    
    # Create deployment script with Azure best practices
    deploy_script_path = os.path.join(azure_dir, 'deploy.ps1' if platform.system() == 'Windows' else 'deploy.sh')
    
    if platform.system() == 'Windows':
        with open(deploy_script_path, 'w') as f:
            f.write('# Azure deployment script for CountyDataSync\n\n')
            f.write('param(\n')
            f.write('    [Parameter(Mandatory=$true)]\n')
            f.write('    [string]$ResourceGroup,\n\n')
            f.write('    [Parameter(Mandatory=$true)]\n')
            f.write('    [string]$AppServiceName,\n\n')
            f.write('    [Parameter(Mandatory=$false)]\n')
            f.write('    [string]$Location = "eastus",\n\n')
            f.write('    [Parameter(Mandatory=$false)]\n')
            f.write('    [bool]$EnableAppInsights = $true\n')
            f.write(')\n\n')
            
            # Azure best practices - Check login status
            f.write('# Check if logged in to Azure\n')
            f.write('$loginStatus = az account show 2>$null\n')
            f.write('if (-not $loginStatus) {\n')
            f.write('    Write-Host "Not logged in to Azure. Please run: az login"\n')
            f.write('    exit 1\n')
            f.write('}\n\n')
            
            # Azure best practices - Check if resource group exists
            f.write('# Check if resource group exists, create if not\n')
            f.write('$rgExists = az group exists --name $ResourceGroup\n')
            f.write('if ($rgExists -eq "false") {\n')
            f.write('    Write-Host "Creating resource group $ResourceGroup in $Location"\n')
            f.write('    az group create --name $ResourceGroup --location $Location\n')
            f.write('}\n\n')
            
            # Azure best practices - Add App Insights for monitoring
            f.write('# Create Application Insights if enabled\n')
            f.write('if ($EnableAppInsights) {\n')
            f.write('    $appInsightsName = "${AppServiceName}-insights"\n')
            f.write('    Write-Host "Creating Application Insights $appInsightsName"\n')
            f.write('    $appInsightsKey = (az monitor app-insights component create --app $appInsightsName --location $Location --kind web --resource-group $ResourceGroup --application-type web --query "instrumentationKey" -o tsv)\n')
            f.write('}\n\n')
            
            # Deploy to Azure App Service
            f.write('# Deploy to Azure App Service\n')
            f.write('Write-Host "Deploying application to $AppServiceName..."\n')
            f.write('az webapp deployment source config-zip --resource-group $ResourceGroup --name $AppServiceName --src "../CountyDataSync.zip"\n\n')
            
            # Azure best practices - Configure app settings
            f.write('# Configure app settings\n')
            f.write('$settings = ""\n')
            f.write('if ($EnableAppInsights -and $appInsightsKey) {\n')
            f.write('    $settings = "APPINSIGHTS_INSTRUMENTATIONKEY=$appInsightsKey APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=$appInsightsKey ApplicationInsightsAgent_EXTENSION_VERSION=~2"\n')
            f.write('}\n\n')
            f.write('if ($settings) {\n')
            f.write('    Write-Host "Configuring application settings"\n')
            f.write('    az webapp config appsettings set --resource-group $ResourceGroup --name $AppServiceName --settings $settings\n')
            f.write('}\n\n')
            
            # Print deployment info
            f.write('# Get the deployed app URL\n')
            f.write('$appUrl = az webapp show --resource-group $ResourceGroup --name $AppServiceName --query "defaultHostName" -o tsv\n')
            f.write('Write-Host "Deployment completed successfully!"\n')
            f.write('Write-Host "Your app is available at: https://$appUrl"\n')
    else:
        with open(deploy_script_path, 'w') as f:
            f.write('#!/bin/bash\n\n')
            f.write('# Azure deployment script for CountyDataSync\n\n')
            f.write('if [ "$#" -lt 2 ]; then\n')
            f.write('    echo "Usage: ./deploy.sh <resource-group> <app-service-name> [location] [enable-app-insights]"\n')
            f.write('    exit 1\n')
            f.write('fi\n\n')
            f.write('RESOURCE_GROUP=$1\n')
            f.write('APP_SERVICE_NAME=$2\n')
            f.write('LOCATION=${3:-"eastus"}\n')
            f.write('ENABLE_APP_INSIGHTS=${4:-true}\n\n')
            
            # Azure best practices - Check login status
            f.write('# Check if logged in to Azure\n')
            f.write('if ! az account show >/dev/null 2>&1; then\n')
            f.write('    echo "Not logged in to Azure. Please run: az login"\n')
            f.write('    exit 1\n')
            f.write('fi\n\n')
            
            # Azure best practices - Check if resource group exists
            f.write('# Check if resource group exists, create if not\n')
            f.write('if [ "$(az group exists --name "$RESOURCE_GROUP")" = "false" ]; then\n')
            f.write('    echo "Creating resource group $RESOURCE_GROUP in $LOCATION"\n')
            f.write('    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"\n')
            f.write('fi\n\n')
            
            # Azure best practices - Add App Insights for monitoring
            f.write('# Create Application Insights if enabled\n')
            f.write('if [ "$ENABLE_APP_INSIGHTS" = true ]; then\n')
            f.write('    APP_INSIGHTS_NAME="${APP_SERVICE_NAME}-insights"\n')
            f.write('    echo "Creating Application Insights $APP_INSIGHTS_NAME"\n')
            f.write('    APP_INSIGHTS_KEY=$(az monitor app-insights component create --app "$APP_INSIGHTS_NAME" \\\n')
            f.write('        --location "$LOCATION" --kind web --resource-group "$RESOURCE_GROUP" \\\n')
            f.write('        --application-type web --query "instrumentationKey" -o tsv)\n')
            f.write('fi\n\n')
            
            # Deploy to Azure App Service
            f.write('# Deploy to Azure App Service\n')
            f.write('echo "Deploying application to $APP_SERVICE_NAME..."\n')
            f.write('az webapp deployment source config-zip --resource-group "$RESOURCE_GROUP" --name "$APP_SERVICE_NAME" --src "../CountyDataSync.zip"\n\n')
            
            # Azure best practices - Configure app settings
            f.write('# Configure app settings\n')
            f.write('if [ "$ENABLE_APP_INSIGHTS" = true ] && [ -n "$APP_INSIGHTS_KEY" ]; then\n')
            f.write('    echo "Configuring application settings"\n')
            f.write('    az webapp config appsettings set --resource-group "$RESOURCE_GROUP" --name "$APP_SERVICE_NAME" \\\n')
            f.write('        --settings "APPINSIGHTS_INSTRUMENTATIONKEY=$APP_INSIGHTS_KEY" \\\n')
            f.write('        "APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=$APP_INSIGHTS_KEY" \\\n')
            f.write('        "ApplicationInsightsAgent_EXTENSION_VERSION=~2"\n')
            f.write('fi\n\n')
            
            # Print deployment info
            f.write('# Get the deployed app URL\n')
            f.write('APP_URL=$(az webapp show --resource-group "$RESOURCE_GROUP" --name "$APP_SERVICE_NAME" --query "defaultHostName" -o tsv)\n')
            f.write('echo "Deployment completed successfully!"\n')
            f.write('echo "Your app is available at: https://$APP_URL"\n')
        
        # Make the script executable
        os.chmod(deploy_script_path, 0o755)
    
    # Create Azure ARM template with best practices
    arm_template_path = os.path.join(azure_dir, 'template.json')
    arm_template = {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
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
            },
            "enableAppInsights": {
                "type": "bool",
                "defaultValue": True,
                "metadata": {
                    "description": "Enable Application Insights monitoring"
                }
            }
        },
        "variables": {
            "appServicePlanName": "[concat(parameters('appServiceName'), '-plan')]",
            "appInsightsName": "[concat(parameters('appServiceName'), '-insights')]"
        },
        "resources": [
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
                    "reserved": False
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
                    "httpsOnly": True,
                    "siteConfig": {
                        "alwaysOn": True,
                        "minTlsVersion": "1.2",
                        "httpLoggingEnabled": True,
                        "detailedErrorLoggingEnabled": True
                    }
                },
                "identity": {
                    "type": "SystemAssigned"
                }
            },
            {
                "condition": "[parameters('enableAppInsights')]",
                "type": "Microsoft.Insights/components",
                "apiVersion": "2020-02-02",
                "name": "[variables('appInsightsName')]",
                "location": "[parameters('location')]",
                "kind": "web",
                "properties": {
                    "Application_Type": "web",
                    "Request_Source": "rest",
                    "RetentionInDays": 90,
                    "publicNetworkAccessForIngestion": "Enabled",
                    "publicNetworkAccessForQuery": "Enabled"
                }
            }
        ],
        "outputs": {
            "appServiceUrl": {
                "type": "string",
                "value": "[concat('https://', reference(resourceId('Microsoft.Web/sites', parameters('appServiceName'))).defaultHostName)]"
            },
            "appServiceIdentityPrincipalId": {
                "condition": True,
                "type": "string",
                "value": "[reference(resourceId('Microsoft.Web/sites', parameters('appServiceName')), '2021-02-01', 'Full').identity.principalId]"
            }
        }
    }
    
    with open(arm_template_path, 'w') as f:
        json.dump(arm_template, f, indent=2)
    
    # Create Azure environment configuration file
    azure_env_path = os.path.join(azure_dir, '.env.azure.example')
    with open(azure_env_path, 'w') as f:
        f.write("# Azure Environment Configuration\n\n")
        f.write("# Rename this file to .env before deploying to Azure\n\n")
        f.write("# Azure App Service specific settings\n")
        f.write("WEBSITE_RUN_FROM_PACKAGE=1\n")
        f.write("WEBSITES_PORT=8000\n\n")
        f.write("# Application settings\n")
        f.write("ASPNETCORE_ENVIRONMENT=Production\n")
        f.write("DATABASE_URL=YOUR_DATABASE_CONNECTION_STRING\n")
        f.write("MSSQL_SERVER=your-server.database.windows.net\n")
        f.write("MSSQL_DATABASE=your-database\n")
        f.write("MSSQL_USERNAME=your-username\n")
        f.write("MSSQL_PASSWORD=your-password\n\n")
        f.write("# Managed Identity and Key Vault Integration\n")
        f.write("# USE_MANAGED_IDENTITY=true\n")
        f.write("# KEY_VAULT_URL=https://your-vault.vault.azure.net/\n")
    
    print(f"✓ Created Azure deployment files in {azure_dir}")
    print("✓ Created Azure ARM template with security best practices")
    print("✓ Included Application Insights for monitoring")
    print("✓ Added Managed Identity configuration options")

def create_directory_structure(dist_dir):
    """Create necessary directories in the distribution package."""
    print("\nCreating directory structure...")
    
    # Create directories
    for directory in ['logs', 'output', 'data', 'config', 'temp']:
        os.makedirs(os.path.join(dist_dir, directory), exist_ok=True)
        print(f"✓ Created {directory} directory")
    
    # Create a .keep file in each directory
    for directory in ['logs', 'output', 'data', 'config', 'temp']:
        with open(os.path.join(dist_dir, directory, '.keep'), 'w') as f:
            f.write("# This file ensures the directory is included in the package\n")

def test_packaged_executable(dist_dir):
    """Test the packaged executable."""
    print("\nTesting packaged executable...")
    exe_name = 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else '')
    exe_path = os.path.join(dist_dir, exe_name)
    
    if not os.path.exists(exe_path):
        print(f"❌ Executable not found at {exe_path}")
        return False
    
    try:
        # Create a temporary .env file for testing
        env_path = os.path.join(dist_dir, '.env')
        with open(env_path, 'w') as f:
            f.write("# Test environment configuration\n")
            f.write("USE_TEST_DATA=true\n")
            f.write("TEST_MODE=true\n")
        
        # Run the executable with --test flag (assuming it supports this)
        print(f"Running {exe_path} --test")
        
        # Use subprocess.run with error handling
        try:
            result = subprocess.run([exe_path, '--test'], 
                                  cwd=dist_dir,
                                  capture_output=True,     
                                  text=True, 
                                  timeout=60)
            
            # Check the output for success indicators
            if result.returncode == 0 and "Test completed successfully" in result.stdout:
                print("✓ Executable test passed!")
                return True
            else:
                print(f"❌ Executable test failed with return code {result.returncode}")
                print("--- STDOUT ---")
                print(result.stdout)
                print("--- STDERR ---")
                print(result.stderr)
                return False
        except FileNotFoundError:
            print(f"❌ Could not execute {exe_path}. Make sure it's executable.")
            return False
        except subprocess.TimeoutExpired:
            print("❌ Executable test timed out (60 seconds)")
            return False
        except Exception as e:
            print(f"❌ Error testing executable: {str(e)}")
            return False
    finally:
        # Clean up test environment file
        if os.path.exists(env_path):
            os.remove(env_path)

def create_platform_installer(dist_dir, version):
    """Create platform-specific installer."""
    print("\nCreating platform-specific installer...")
    
    if platform.system() == 'Windows':
        return create_windows_installer(dist_dir, version)
    elif platform.system() == 'Darwin':  # macOS
        return create_macos_installer(dist_dir, version)
    else:  # Linux
        print("No installer creation is implemented for Linux.")
        return False

def create_windows_installer(dist_dir, version):
    """Create Windows installer using NSIS."""
    try:
        # Check if NSIS is installed
        nsis_path = shutil.which('makensis')
        if not nsis_path:
            print("❌ NSIS not found. Please install it from https://nsis.sourceforge.io/")
            return False
        
        # Check for NSIS script template
        nsis_template = 'installers/windows_installer.nsi'
        if not os.path.exists(nsis_template):
            print(f"❌ NSIS script template not found at {nsis_template}")
            return False
        
        # Create a temp copy of the NSIS script with proper version
        temp_nsis = 'installers/temp_installer.nsi'
        with open(nsis_template, 'r') as src, open(temp_nsis, 'w') as dst:
            content = src.read()
            content = content.replace('{{VERSION}}', version)
            content = content.replace('{{SOURCE_DIR}}', os.path.abspath(dist_dir))
            content = content.replace('{{OUTPUT_FILE}}', f'CountyDataSync-{version}-Setup.exe')
            dst.write(content)
        
        print("Running NSIS compiler...")
        result = subprocess.run([nsis_path, temp_nsis], 
                               check=True, capture_output=True, text=True)
        
        installer_path = f'CountyDataSync-{version}-Setup.exe'
        if os.path.exists(installer_path):
            print(f"✓ Windows installer created: {installer_path}")
            return True
        else:
            print("❌ Failed to create Windows installer")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error creating Windows installer: {str(e)}")
        return False
    finally:
        # Clean up temporary files
        if os.path.exists(temp_nsis):
            os.remove(temp_nsis)

def create_macos_installer(dist_dir, version):
    """Create macOS DMG installer."""
    try:
        # Check if create-dmg is installed
        create_dmg_path = shutil.which('create-dmg')
        if not create_dmg_path:
            print("❌ create-dmg not found. Install with: brew install create-dmg")
            return False
        
        # Create DMG
        dmg_path = f'CountyDataSync-{version}.dmg'
        cmd = [
            create_dmg_path,
            '--volname', f'CountyDataSync {version}',
            '--volicon', 'assets/icon.icns',
            '--window-pos', '200', '100',
            '--window-size', '800', '400',
            '--icon-size', '100',
            '--icon', 'CountyDataSync.app', '200', '200',
            '--app-drop-link', '600', '200',
            dmg_path,
            os.path.abspath(dist_dir)
        ]
        
        print("Creating DMG installer...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if os.path.exists(dmg_path):
            print(f"✓ macOS installer created: {dmg_path}")
            return True
        else:
            print("❌ Failed to create macOS installer")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error creating macOS installer: {str(e)}")
        return False

def create_distribution_package(version):
    """Create distribution package."""
    print("\nCreating distribution package...")
    
    # Define paths
    exe_name = 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else '')
    exe_path = os.path.join('dist', exe_name)
    
    # Check if executable exists
    if not os.path.exists(exe_path):
        print(f"❌ Error: Executable not found at {exe_path}")
        return False
    
    dist_dir = f'CountyDataSync-{version}'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Copy executable
    shutil.copy2(exe_path, os.path.join(dist_dir, exe_name))
    print(f"✓ Copied executable to {dist_dir}")
    
    # Create directory structure
    create_directory_structure(dist_dir)
    
    # Copy documentation
    copy_documentation(dist_dir)
    
    # Copy configuration files
    copy_config_files(dist_dir)
    
    # Create version file
    with open(os.path.join(dist_dir, 'version.txt'), 'w') as f:
        f.write(f"CountyDataSync version {version}\n")
        f.write(f"Built on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test the executable if requested
    if args.test:
        if not test_packaged_executable(dist_dir):
            print("⚠️ Executable testing failed!")
    
    # Create platform-specific installer if requested
    if args.installer:
        create_platform_installer(dist_dir, version)
    
    # Create zip archive
    zip_filename = f'{dist_dir}.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(dist_dir)))
    
    print(f"\n✅ Distribution package created: {zip_filename}")
    return True

def main():
    """Main entry point."""
    global args
    # Parse arguments
    args = parse_arguments()
    
    print("=" * 60)
    print(f"CountyDataSync Packaging (Version: {args.version})")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisite check failed. Please fix the issues and try again.")
        sys.exit(1)
    
    # Check spec file if we're building
    if not args.check_only and not check_spec_file():
        print("\n⚠️ Spec file issues detected. You may need to create or update it.")
    
    # If only checking prerequisites, exit here
    if args.check_only:
        print("\n✅ All checks completed. Use --check-only flag to skip packaging.")
        sys.exit(0)
    
    # Build executable if it doesn't exist
    exe_path = os.path.join('dist', 'CountyDataSync' + ('.exe' if platform.system() == 'Windows' else ''))
    if not os.path.exists(exe_path):
        if not build_executable():
            print("\n❌ Aborting package creation due to build failures.")
            sys.exit(1)
    else:
        print(f"\n✓ Using existing executable at {exe_path}")
    
    # Create distribution package
    if create_distribution_package(args.version):
        print("\n✅ Packaging completed successfully!")
    else:
        print("\n❌ Packaging failed.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("\nIf you're seeing Python path-related errors:")
        print("1. Make sure Python is installed and in your PATH")
        print("2. Try running this script with the full path to Python")
        print("   Example: C:\\Python39\\python.exe package_application.py")
        sys.exit(1)

