"""
Health check script for CountyDataSync database files.

This script verifies the integrity of database files by checking
if tables exist and have records.
"""
import sqlite3
import os
import sys
import logging
import geopandas as gpd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_sqlite_table(db_file, table):
    """
    Check if a table exists and has records in an SQLite database.
    
    Args:
        db_file (str): Path to the SQLite database file
        table (str): Name of the table to check
        
    Returns:
        int: Number of records in the table, or 0 if the file doesn't exist
    """
    if not os.path.exists(db_file):
        logger.warning(f"Database file {db_file} not found")
        return 0
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cursor.fetchone():
            logger.warning(f"Table {table} does not exist in {db_file}")
            conn.close()
            return 0
        
        # Count records in the table
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except sqlite3.Error as e:
        logger.error(f"SQLite error in {db_file}: {str(e)}")
        return 0

def check_geopackage(gpkg_file):
    """
    Check if a GeoPackage file exists and has data.
    
    Args:
        gpkg_file (str): Path to the GeoPackage file
        
    Returns:
        int: Number of features in the GeoPackage, or 0 if the file doesn't exist
    """
    if not os.path.exists(gpkg_file):
        logger.warning(f"GeoPackage file {gpkg_file} not found")
        return 0
    
    try:
        # Try to read the GeoPackage
        gdf = gpd.read_file(gpkg_file)
        return len(gdf)
    except Exception as e:
        logger.error(f"Error reading GeoPackage {gpkg_file}: {str(e)}")
        return 0

def run_health_check():
    """
    Run health checks on all database files.
    
    Returns:
        bool: True if all checks pass, False otherwise
    """
    health_status = True
    
    # Check SQLite databases
    stats_db = 'output/stats_db.sqlite'
    working_db = 'output/working_db.sqlite'
    geo_db = 'output/geo_db.gpkg'
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Check stats database
    stats_count = check_sqlite_table(stats_db, 'stats')
    logger.info(f"Stats table record count: {stats_count}")
    
    # Check working database
    working_count = check_sqlite_table(working_db, 'working_data')
    logger.info(f"Working data table record count: {working_count}")
    
    # Check geo database
    geo_count = check_geopackage(geo_db)
    logger.info(f"GeoPackage feature count: {geo_count}")
    
    # Evaluate overall health
    if os.path.exists(stats_db) and stats_count == 0:
        logger.error(f"Health check failed: Stats database exists but is empty")
        health_status = False
        
    if os.path.exists(working_db) and working_count == 0:
        logger.error(f"Health check failed: Working database exists but is empty")
        health_status = False
        
    if os.path.exists(geo_db) and geo_count == 0:
        logger.error(f"Health check failed: GeoPackage exists but is empty")
        health_status = False
    
    return health_status

if __name__ == "__main__":
    try:
        logger.info("Starting health check...")
        if run_health_check():
            logger.info("Health check passed.")
            sys.exit(0)
        else:
            logger.error("Health check failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        sys.exit(1)