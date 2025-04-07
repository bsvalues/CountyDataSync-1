"""
Configuration module for CountyDataSync ETL process.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# SQL Server configuration
SQL_SERVER_CONFIG = {
    'server': os.getenv('SQL_SERVER_HOST', 'localhost'),
    'database': os.getenv('SQL_DATABASE', 'master'),
    'username': os.getenv('SQL_USERNAME', 'sa'),
    'password': os.getenv('SQL_PASSWORD', ''),
    'driver': os.getenv('SQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
}

# Output paths
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
OUTPUT_PATHS = {
    'geo_db': os.path.join(OUTPUT_DIR, os.getenv('GEO_DB_NAME', 'geo_db.gpkg')),
    'stats_db': os.path.join(OUTPUT_DIR, os.getenv('STATS_DB_NAME', 'stats_db.sqlite')),
    'working_db': os.path.join(OUTPUT_DIR, os.getenv('WORKING_DB_NAME', 'working_db.sqlite'))
}

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Batch settings
DEFAULT_BATCH_SIZE = int(os.getenv('DEFAULT_BATCH_SIZE', '1000'))

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'etl_process.log')

# CRS (Coordinate Reference System) settings
# Default to WGS 84 (EPSG:4326) if not specified
DEFAULT_CRS = os.getenv('DEFAULT_CRS', 'EPSG:4326')

# Additional settings for performance tuning
MAX_MEMORY_USAGE_MB = int(os.getenv('MAX_MEMORY_USAGE_MB', '1024'))
