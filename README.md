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

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Build the executable:
   ```
   python build_executable.py
   ```
3. Find the executable in the `dist_package` directory

## Configuration

Before running the ETL process, you need to configure the connection to your SQL Server and output settings. Copy the `.env.example` file to `.env` and edit it with your specific settings:

