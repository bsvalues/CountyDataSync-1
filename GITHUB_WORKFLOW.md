# GitHub Actions Workflow for CountyDataSync

This document contains the full GitHub Actions workflow configuration that should be placed in the `.github/workflows/ci-cd.yml` file of your repository.

## Workflow Configuration

```yaml
name: CI/CD - CountyDataSync Enhanced Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # For scheduled tasks like backups or health checks

jobs:
  build-test-package:
    name: Build, Test, and Package CountyDataSync
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Set up Python Environment
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
          pip install pyinstaller
          pip install python-dotenv

      - name: Generate Application Icon
        run: python generate_icon.py

      - name: Generate Spec File
        run: python generate_spec.py

      - name: Run Unit and Integration Tests
        run: |
          python -m pytest tests/ --maxfail=1 --disable-warnings -q

      - name: Package with PyInstaller
        run: python build_executable.py

      - name: Run ETL with Test Data
        run: |
          # Set environment variables
          echo "USE_TEST_DATA=true" >> $GITHUB_ENV
          python sync.py --test-data

      - name: Run Health Check
        run: python health_check.py

      - name: Upload Executable Artifact
        uses: actions/upload-artifact@v3
        with:
          name: county-data-sync-executable
          path: dist/CountyDataSync*
          
      - name: Archive Logs
        uses: actions/upload-artifact@v3
        with:
          name: logs
          path: logs/
  
  backup:
    name: Scheduled Database Backup
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt
          pip install python-dotenv

      - name: Run ETL with Test Data
        run: |
          echo "USE_TEST_DATA=true" >> $GITHUB_ENV
          python sync.py --test-data

      - name: Run Backup Script
        run: python backup_script.py

      - name: Upload Backup Artifact
        uses: actions/upload-artifact@v3
        with:
          name: database-backups
          path: backup/

  # Deployment job - commented out for now, uncomment and customize for your deployment
  # deploy:
  #   name: Deploy to Production
  #   runs-on: ubuntu-latest
  #   needs: build-test-package
  #   if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  #   
  #   steps:
  #     - name: Download Executable Artifact
  #       uses: actions/download-artifact@v3
  #       with:
  #         name: county-data-sync-executable
  #         path: executable
  #         
  #     - name: Deploy to Server
  #       env:
  #         DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
  #         DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
  #         DEPLOY_PATH: ${{ secrets.DEPLOY_PATH }}
  #         SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
  #       run: |
  #         # Setup SSH key
  #         mkdir -p ~/.ssh
  #         echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
  #         chmod 600 ~/.ssh/id_rsa
  #         
  #         # Deploy using SCP
  #         scp -o StrictHostKeyChecking=no executable/CountyDataSync* $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH
  #         
  #         # Optional: Restart service or perform other post-deployment steps
  #         ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST "cd $DEPLOY_PATH && ./restart_service.sh"
```

## Setting Up Secrets

Before using this workflow, you need to configure the following GitHub repository secrets:

1. **For the deployment job (when uncommented):**
   - `DEPLOY_USER`: Username for SSH access to the deployment server
   - `DEPLOY_HOST`: Hostname or IP address of the deployment server
   - `DEPLOY_PATH`: Path on the server where files should be deployed
   - `SSH_PRIVATE_KEY`: Private SSH key for authentication

2. **Optional additional secrets:**
   - `SENTRY_DSN`: If using Sentry for error tracking

## Implementation Steps

1. Create the `.github/workflows` directory in your repository
2. Create a new file named `ci-cd.yml` in that directory
3. Copy the YAML configuration above into the file
4. Commit and push the changes to your repository
5. Configure the required secrets in your GitHub repository settings

## Using GitHub Artifacts

The workflow automatically uploads two types of artifacts:

1. **Executable artifacts**: The packaged CountyDataSync application
2. **Log artifacts**: Application logs generated during tests
3. **Backup artifacts**: Database backups (only from scheduled runs)

These artifacts can be downloaded from the GitHub Actions workflow run page and retained according to your repository settings.

## Customizing the Workflow

You may need to customize this workflow based on:

- Your specific deployment requirements
- Additional testing or validation steps
- Environment-specific configurations
- Additional dependencies or build steps

The deployment job is provided as a template but is commented out - uncomment and customize it based on your specific deployment needs.