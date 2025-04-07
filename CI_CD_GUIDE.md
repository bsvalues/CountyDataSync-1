# CountyDataSync CI/CD Guide

This guide outlines the Continuous Integration and Continuous Deployment (CI/CD) process for the CountyDataSync ETL application.

## CI/CD Goals

1. **Automated Testing**: Validate code quality and functionality
2. **Automated Builds**: Create standalone executables with PyInstaller
3. **Deployment Process**: Streamline deployment to production servers
4. **Monitoring**: Track application health and performance
5. **Backup Strategy**: Automate database backups

## GitHub Actions Workflow

The CI/CD pipeline is implemented using GitHub Actions. The workflow file is located at `.github/workflows/ci-cd.yml`.

### Build, Test, and Package Job

This job runs on every push to the main branch and on pull requests:

1. Set up Python environment
2. Install dependencies
3. Generate application icon
4. Generate PyInstaller spec file
5. Run unit and integration tests
6. Package with PyInstaller
7. Run ETL with test data
8. Run health check
9. Upload executable as artifact

### Backup Job

This job runs on a schedule (daily at 2 AM UTC):

1. Run ETL with test data (to ensure fresh data for backup)
2. Run backup script
3. Upload backup as artifact

### Deployment Job (Optional)

This job can be uncommented and customized for your deployment process:

1. Download executable artifact
2. Deploy to production server using SCP
3. Restart service on server

## Setting Up Secrets

The following secrets should be configured in GitHub:

- `DEPLOY_USER`: SSH username for deployment
- `DEPLOY_HOST`: SSH hostname for deployment
- `DEPLOY_PATH`: Deployment directory on server
- `SSH_PRIVATE_KEY`: SSH private key for deployment

## Local CI/CD Testing

You can test the CI/CD workflow locally before pushing:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Generate icon and spec file
python generate_icon.py
python generate_spec.py

# Build executable
python build_executable.py

# Run health check
python health_check.py

# Run backup script
python backup_script.py
```

## Maintenance Tasks

- **Database Backup**: Daily automatic backups via scheduled workflow
- **Health Checks**: Run on every build and can be scheduled separately
- **Performance Monitoring**: Integrated into the ETL process
- **Log Rotation**: Implemented in deployed environment

## Troubleshooting CI/CD Issues

- Check workflow logs in GitHub Actions
- Review test failure details
- Verify environment variables and secrets
- Test build process locally