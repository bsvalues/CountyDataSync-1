"""
Data validation module for CountyDataSync ETL process.
Provides validation rules for checking data quality and integrity.
"""
import logging
import pandas as pd
import geopandas as gpd
import sqlite3
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/data_validation.log'
)
logger = logging.getLogger(__name__)

def validate_parcel_data(df):
    """
    Validate parcel data against business rules.
    
    Args:
        df (pd.DataFrame): DataFrame with parcel data
        
    Returns:
        dict: Validation results with errors and warnings
    """
    results = {
        'errors': [],
        'warnings': [],
        'record_count': len(df),
        'passed': True
    }
    
    # Check for required columns
    required_columns = ['parcel_id', 'geometry', 'land_use', 'land_value']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        results['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
        results['passed'] = False
    
    # Check for null values in critical columns
    if 'parcel_id' in df.columns:
        null_parcel_ids = df['parcel_id'].isnull().sum()
        if null_parcel_ids > 0:
            results['errors'].append(f"Found {null_parcel_ids} records with null parcel_id")
            results['passed'] = False
    
    # Check for duplicate parcel IDs
    if 'parcel_id' in df.columns:
        duplicate_ids = df['parcel_id'].duplicated().sum()
        if duplicate_ids > 0:
            results['errors'].append(f"Found {duplicate_ids} duplicate parcel IDs")
            results['passed'] = False
    
    # Check for geometries (if this is a GeoDataFrame)
    if isinstance(df, gpd.GeoDataFrame) and 'geometry' in df.columns:
        invalid_geoms = df.geometry.is_valid.value_counts().get(False, 0)
        if invalid_geoms > 0:
            results['errors'].append(f"Found {invalid_geoms} invalid geometries")
            results['passed'] = False
    
    # Check for outliers in land_value (if present)
    if 'land_value' in df.columns:
        # Use IQR method to find outliers
        Q1 = df['land_value'].quantile(0.25)
        Q3 = df['land_value'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - (1.5 * IQR)
        upper_bound = Q3 + (1.5 * IQR)
        outliers = df[(df['land_value'] < lower_bound) | (df['land_value'] > upper_bound)]
        
        if len(outliers) > 0:
            outlier_percentage = (len(outliers) / len(df)) * 100
            results['warnings'].append(
                f"Found {len(outliers)} outliers in land_value ({outlier_percentage:.2f}%)"
            )
    
    # Log validation results
    if results['passed']:
        logger.info(f"Validation passed: {results['record_count']} records processed")
    else:
        logger.error(f"Validation failed: {results['errors']}")
        if results['warnings']:
            logger.warning(f"Validation warnings: {results['warnings']}")
    
    return results

def validate_stats_db(db_path):
    """
    Validate the statistics database structure and contents.
    
    Args:
        db_path (str): Path to the SQLite stats database
        
    Returns:
        dict: Validation results
    """
    results = {
        'errors': [],
        'warnings': [],
        'passed': True
    }
    
    if not os.path.exists(db_path):
        results['errors'].append(f"Stats database not found at {db_path}")
        results['passed'] = False
        return results
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['parcel_stats', 'land_use_summary']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            results['errors'].append(f"Missing required tables: {', '.join(missing_tables)}")
            results['passed'] = False
        
        # Check if tables have data
        for table in [t for t in required_tables if t in tables]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count == 0:
                results['warnings'].append(f"Table {table} is empty")
        
        conn.close()
        
    except sqlite3.Error as e:
        results['errors'].append(f"SQLite error: {str(e)}")
        results['passed'] = False
    
    return results

def validate_geo_db(gpkg_path):
    """
    Validate the GeoPackage database.
    
    Args:
        gpkg_path (str): Path to the GeoPackage file
        
    Returns:
        dict: Validation results
    """
    results = {
        'errors': [],
        'warnings': [],
        'passed': True
    }
    
    if not os.path.exists(gpkg_path):
        results['errors'].append(f"GeoPackage not found at {gpkg_path}")
        results['passed'] = False
        return results
    
    try:
        # Open the GeoPackage
        gdf = gpd.read_file(gpkg_path)
        
        # Check for empty GeoPackage
        if len(gdf) == 0:
            results['errors'].append("GeoPackage contains no features")
            results['passed'] = False
            return results
        
        # Check for valid geometries
        invalid_geoms = ~gdf.geometry.is_valid
        if invalid_geoms.any():
            invalid_count = invalid_geoms.sum()
            results['errors'].append(f"Found {invalid_count} invalid geometries in GeoPackage")
            results['passed'] = False
        
        # Check for required attributes
        required_columns = ['parcel_id', 'land_use']
        missing_columns = [col for col in required_columns if col not in gdf.columns]
        if missing_columns:
            results['errors'].append(f"Missing required columns in GeoPackage: {', '.join(missing_columns)}")
            results['passed'] = False
        
    except Exception as e:
        results['errors'].append(f"Error validating GeoPackage: {str(e)}")
        results['passed'] = False
    
    return results

def run_all_validations(parcel_data=None, stats_db_path=None, geo_db_path=None):
    """
    Run all validations on ETL data and outputs.
    
    Args:
        parcel_data (pd.DataFrame, optional): DataFrame with parcel data
        stats_db_path (str, optional): Path to the stats database
        geo_db_path (str, optional): Path to the GeoPackage
        
    Returns:
        dict: Combined validation results
    """
    results = {
        'parcel_data': None,
        'stats_db': None,
        'geo_db': None,
        'all_passed': True
    }
    
    # Validate parcel data if provided
    if parcel_data is not None:
        results['parcel_data'] = validate_parcel_data(parcel_data)
        results['all_passed'] &= results['parcel_data']['passed']
    
    # Validate stats DB if path provided
    if stats_db_path is not None:
        results['stats_db'] = validate_stats_db(stats_db_path)
        results['all_passed'] &= results['stats_db']['passed']
    
    # Validate GeoPackage if path provided
    if geo_db_path is not None:
        results['geo_db'] = validate_geo_db(geo_db_path)
        results['all_passed'] &= results['geo_db']['passed']
    
    return results