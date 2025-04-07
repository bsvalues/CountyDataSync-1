# CountyDataSync ETL

A Python-based ETL system for extracting data from SQL Server, transforming it using spatial processing tools, and loading it into three different database formats.

## Overview

CountyDataSync's primary goal is to extract data from a master SQL Server (the MasterParcels table), process it using Python (with Pandas and GeoPandas), and load it into three staging databases:

1. **Geo DB**: A GeoPackage file for storing spatial data
2. **Stats DB**: A SQLite database for aggregated statistics
3. **Working DB**: A SQLite database for temporary/editable data

## Prerequisites

- Python 3.x
- Required Python packages:
  - pandas
  - geopandas
  - pyodbc
  - sqlite3
  - shapely
  - psutil
  - python-dotenv

## Installation

1. Clone the repository
2. Install the required packages:
   ```
   pip install pandas geopandas pyodbc shapely psutil python-dotenv
   ```
3. Create a `.env` file based on the provided `.env.example`

## Configuration

Before running the ETL process, you need to configure the connection to your SQL Server and output settings. Copy the `.env.example` file to `.env` and edit it with your specific settings:

