# CountyDataSync ETL

A Python-based ETL system for extracting data from SQL Server, transforming it using spatial processing tools, and loading it into three different database formats.

## Overview

CountyDataSync's primary goal is to extract data from a master SQL Server (the MasterParcels table), process it using Python (with Pandas and GeoPandas), and load it into three staging databases:

1. **Geo DB**: A GeoPackage file for storing spatial data
2. **Stats DB**: A SQLite database for aggregated statistics
3. **Working DB**: A SQLite database for temporary/editable data

## Features

- **Extract**: Connect to SQL Server and extract data from the MasterParcels table
- **Transform**: Process data using Pandas and GeoPandas, including spatial operations
- **Load**: Create and populate three target databases with processed data
- **Performance Monitoring**: Track memory usage, CPU utilization, and processing time
- **Web Interface**: Manage ETL jobs through a Flask web application
- **Standalone Mode**: Run as a command-line application or package as a standalone executable
- **CI/CD Integration**: Automated testing, packaging, and deployment pipeline

## Prerequisites

- Python 3.10 or later
- Required Python packages:
  - pandas
  - geopandas
  - pyodbc
  - sqlalchemy
  - shapely
  - psutil
  - python-dotenv
  - flask (for web interface)

## Installation

### Method 1: Run as a Python Application

1. Clone the repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on the provided `.env.example`

### Method 2: Run as a Standalone Executable

#### Option A: Using the Packaging Script

1. Install PyInstaller and dependencies:
   ```
   pip install pyinstaller pandas geopandas pyodbc sqlalchemy shapely psutil python-dotenv
   ```
2. Run the packaging readiness check:
   ```
   python check_packaging_readiness.py
   ```
3. Build the executable:
   ```
   python package_application.py --version 1.0.0
   ```
4. Find the packaged application in the created zip file (e.g., `CountyDataSync-1.0.0.zip`)

#### Option B: Manual Packaging

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Build the executable:
   ```
   python build_executable.py
   ```
3. Find the executable in the `dist` directory

For detailed packaging instructions, refer to the [Packaging Guide](PACKAGING.md).

### Method 3: Use the CI/CD Pipeline

The project includes a GitHub Actions workflow for automated building, testing, and packaging:

1. Push your changes to the main branch
2. The CI/CD pipeline automatically:
   - Runs all tests
   - Packages the application with PyInstaller
   - Archives the executable as an artifact
   - Performs database backups (on scheduled runs)
   - Can be configured to deploy to production

See the [CI/CD Guide](CI_CD_GUIDE.md) for detailed information on setting up and customizing the pipeline.

## Configuration

Before running the ETL process, you need to configure the connection to your SQL Server and output settings. Copy the `.env.example` file to `.env` and edit it with your specific settings:

