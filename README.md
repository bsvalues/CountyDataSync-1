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

# CountyDataSync Backup Tool

A comprehensive backup solution for CountyDataSync databases with optional Azure Blob Storage support.

## Features

- Backs up multiple database types (SQLite, GeoPackage)
- Performs integrity checks before backup
- Creates compressed archives of backups
- Supports local storage and Azure Blob Storage
- Configurable retention policy for automatic cleanup
- Detailed logging and reporting

## Installation

1. Ensure Python 3.6+ is installed
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `config.ini.example` to `config.ini` and modify as needed

## Usage

Basic usage:
```
python backup_script.py
```

With options:
```
python backup_script.py --config /path/to/config.ini --backup-dir /path/to/backups --retention 30 --verbose --azure
```

Options:
- `--config`: Path to configuration file (defaults to built-in defaults)
- `--backup-dir`: Directory to store backups
- `--retention`: Number of days to retain backups (0 to disable cleanup)
- `--verbose`: Enable verbose logging
- `--azure`: Enable Azure Blob Storage backup

## Azure Blob Storage Setup

To enable Azure Blob Storage backup:

1. Create an Azure Storage account
2. Get your connection string from the Azure Portal
3. Add it to your config.ini file
4. Set `enabled = true` in the Azure section

## Deployment Recommendations

### Running as a Scheduled Task (Windows)

1. Open Task Scheduler
2. Create a Basic Task
3. Set trigger (e.g., daily at 2 AM)
4. Action: Start a program
5. Program/script: `python`
6. Arguments: `/path/to/backup_script.py --config /path/to/config.ini`

### Running as a Cron Job (Linux)

Add to crontab:
```
0 2 * * * /usr/bin/python3 /path/to/backup_script.py --config /path/to/config.ini
```

### Running in Docker

A Dockerfile is available in the repository. Build and run:
```
docker build -t countydatasync-backup .
docker run -v /path/to/data:/app/data -v /path/to/backups:/app/backups countydatasync-backup
```

