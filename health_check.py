#!/usr/bin/env python3
"""
Health check script for CountyDataSync database files.

This script verifies the integrity of database files by checking
if tables exist and have records.
"""
import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

import geopandas as gpd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health_check.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('HealthCheck')

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
        logger.warning(f"Database file not found: {db_file}")
        return 0
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cursor.fetchone():
            logger.warning(f"Table '{table}' not found in {db_file}")
            conn.close()
            return 0
        
        # Count records
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        
        logger.info(f"Table '{table}' in {db_file} has {count} records")
        return count
    
    except sqlite3.Error as e:
        logger.error(f"SQLite error in {db_file}: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error checking {db_file}: {e}")
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
        logger.warning(f"GeoPackage file not found: {gpkg_file}")
        return 0
    
    try:
        # Read the GeoPackage and count features
        gdf = gpd.read_file(gpkg_file)
        count = len(gdf)
        
        logger.info(f"GeoPackage {gpkg_file} has {count} features")
        return count
    
    except Exception as e:
        logger.error(f"Error reading GeoPackage {gpkg_file}: {e}")
        return 0

def run_health_check():
    """
    Run health checks on all database files.
    
    Returns:
        bool: True if all checks pass, False otherwise
    """
    # Define output directory
    output_dir = Path('output')
    if not output_dir.exists():
        logger.warning(f"Output directory not found: {output_dir}")
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
    
    # Define expected files and tables
    checks = [
        {'type': 'geopackage', 'file': output_dir / 'parcels.gpkg'},
        {'type': 'sqlite', 'file': output_dir / 'stats.db', 'table': 'parcel_stats'},
        {'type': 'sqlite', 'file': output_dir / 'working.db', 'table': 'parcels'}
    ]
    
    # Run checks
    results = []
    all_passed = True
    
    for check in checks:
        if check['type'] == 'sqlite':
            count = check_sqlite_table(check['file'], check['table'])
            passed = count > 0
            results.append({
                'file': str(check['file']),
                'type': check['type'],
                'table': check['table'],
                'record_count': count,
                'passed': passed
            })
            all_passed = all_passed and passed
        
        elif check['type'] == 'geopackage':
            count = check_geopackage(check['file'])
            passed = count > 0
            results.append({
                'file': str(check['file']),
                'type': check['type'],
                'record_count': count,
                'passed': passed
            })
            all_passed = all_passed and passed
    
    # Log and save results
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = f'logs/health_check_{timestamp}.json'
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'all_passed': all_passed,
            'checks': results
        }, f, indent=2)
    
    if all_passed:
        logger.info("All health checks passed!")
    else:
        logger.warning("Some health checks failed. See report for details.")
    
    logger.info(f"Health check report saved to {report_file}")
    return all_passed

if __name__ == "__main__":
    logger.info("Starting health check...")
    success = run_health_check()
    logger.info("Health check completed.")
    
    # Return appropriate exit code for CI/CD pipelines
    sys.exit(0 if success else 1)