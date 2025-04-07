# Packaging Guide for CountyDataSync

This guide explains how to package the CountyDataSync ETL service into a standalone executable using PyInstaller.

## Prerequisites

Before packaging, ensure you have the following:

- Python 3.10 or later installed
- PyInstaller package installed (`pip install pyinstaller`)
- All dependencies listed in `pyproject.toml` installed

## Packaging Steps

### Method 1: Using the Build Script

The easiest way to package the application is to use the included build script:

```bash
python build_executable.py
```

This script:
1. Checks if PyInstaller is installed (and installs it if necessary)
2. Runs PyInstaller with the appropriate options
3. Creates a distribution package in the `dist_package` directory

### Method 2: Manual PyInstaller Command

You can also run PyInstaller manually with the following command:

```bash
pyinstaller --onefile --clean --name CountyDataSync --add-data "etl:etl" --add-data ".env.example:." --hidden-import etl --hidden-import etl.extract --hidden-import etl.transform --hidden-import etl.load --hidden-import etl.sync --hidden-import etl.utils --hidden-import etl.test_data --hidden-import pandas --hidden-import geopandas --hidden-import shapely --hidden-import numpy --hidden-import pyodbc --hidden-import sqlalchemy --hidden-import dotenv --hidden-import psutil sync.py
```

Note: On Windows, use `;` instead of `:` in the `--add-data` options.

## Distribution Structure

After packaging, you should have a distribution package with the following files:

- `CountyDataSync` (or `CountyDataSync.exe` on Windows): The standalone executable
- `README.txt`: Usage instructions
- `.env.example`: Example environment variables

## Running the Packaged Application

The packaged application can be run directly:

```bash
./CountyDataSync --test-data
```

Or with custom options:

```bash
./CountyDataSync --batch-size 500 --output-dir custom_output --log-level DEBUG
```

## Environment Setup

Before running, configure environment variables either by:

1. Creating a `.env` file in the same directory as the executable
2. Setting environment variables in the system

Example `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost:5432/database
MSSQL_SERVER=sql-server-hostname
MSSQL_DATABASE=county_db
MSSQL_USERNAME=username
MSSQL_PASSWORD=password
```

## Common Issues

### Missing Dependencies

If the executable fails due to missing dependencies, ensure that all required packages are listed in the hidden imports.

### File Not Found Errors

If you encounter "File not found" errors, check that all necessary data files are included with the `--add-data` option.

### SQL Server Connectivity

If SQL Server connection fails:
1. Verify that your environment variables are set correctly
2. Use the `--test-data` flag to run with test data for validation

## Deployment Considerations

### Linux Deployment

When deploying on Linux systems:

1. Ensure the executable has proper permissions:
   ```bash
   chmod +x CountyDataSync
   ```

2. Install required system dependencies:
   ```bash
   sudo apt-get install libgeos-dev unixodbc-dev
   ```

### Windows Deployment

When deploying on Windows systems:

1. Ensure the Microsoft ODBC Driver for SQL Server is installed
2. Install Visual C++ Redistributable if needed